import random
import asyncio
import httpx
import redis.asyncio as aioredis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
from app.config import get_settings

settings = get_settings()

_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        # Upstash idle-closes TCP after ~5min — keepalive + retry survives that.
        kwargs: dict = {
            "decode_responses": True,
            "socket_keepalive": True,
            "health_check_interval": 30,
            "retry_on_error": [RedisConnectionError, RedisTimeoutError],
            "retry": Retry(ExponentialBackoff(cap=1, base=0.1), retries=3),
        }
        if settings.redis_url.startswith("rediss://"):
            kwargs["ssl_cert_reqs"] = "none"
        _redis = aioredis.from_url(settings.redis_url, **kwargs)
    return _redis


def normalise_phone(phone: str) -> str:
    """
    Normalise any Nigerian phone format to E.164 without the + sign.
    08012345678  -> 2348012345678
    +2348012345678 -> 2348012345678
    2348012345678  -> 2348012345678
    """
    p = phone.strip().replace(" ", "").replace("-", "")
    if p.startswith("+"):
        p = p[1:]
    if p.startswith("0") and len(p) == 11:
        p = "234" + p[1:]
    return p


def _otp_key(phone: str) -> str:
    return f"otp:{normalise_phone(phone)}"


def _attempts_key(phone: str) -> str:
    return f"otp_attempts:{normalise_phone(phone)}"


def _generate_otp() -> str:
    return str(random.randint(100000, 999999))


async def send_otp(phone: str) -> bool:
    r = _get_redis()
    normalised = normalise_phone(phone)
    otp_key = _otp_key(normalised)
    attempts_key = _attempts_key(normalised)

    attempts = await r.get(attempts_key)
    if attempts and int(attempts) >= settings.otp_max_attempts:
        return False

    otp = _generate_otp()

    # Pipeline all writes into one network round-trip (Upstash latency matters).
    pipe = r.pipeline()
    pipe.setex(otp_key, settings.otp_expiry_seconds, otp)
    pipe.incr(attempts_key)
    pipe.expire(attempts_key, 3600)
    await pipe.execute()

    # Fire-and-forget: dispatch SMS/WhatsApp in background so API responds instantly
    asyncio.create_task(_dispatch_sms(normalised, otp))
    print(f"[send_otp] queued otp={otp} for {normalised}", flush=True)
    return True


async def verify_otp(phone: str, code: str) -> bool:
    normalised = normalise_phone(phone)
    r = _get_redis()
    stored = await r.get(_otp_key(normalised))
    if stored and stored == code:
        await r.delete(_otp_key(normalised))
        await r.delete(_attempts_key(normalised))
        return True
    return False


async def _dispatch_sms(phone: str, otp: str) -> None:
    # Always print so we can test even if delivery fails
    print(f"[OTP] {phone} -> {otp}", flush=True)

    to = f"+{phone}"
    delivered = False

    # Try Wasender WhatsApp first
    if settings.wasender_api_url and settings.wasender_api_keys:
        await _dispatch_wasender(phone, otp)
    else:
        print("[DEV] No delivery channel configured — OTP printed above only", flush=True)


async def _dispatch_wasender(phone: str, otp: str) -> bool:
    """Returns True if Wasender confirmed delivery."""
    keys = [k.strip() for k in settings.wasender_api_keys.split(",") if k.strip()]
    if not keys:
        print("[Wasender] No valid API keys found", flush=True)
        return False
        
    r = _get_redis()
    idx = await r.incr("wasender_api_key_idx")
    selected_key = keys[idx % len(keys)]

    message = f"Your alwi verification code is {otp}. Valid for 10 minutes. Do not share."
    headers = {
        "Authorization": f"Bearer {selected_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": phone,
        "text": message
    }

    try:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.post(
                settings.wasender_api_url,
                json=payload,
                headers=headers,
            )
        print(f"[Wasender] status={resp.status_code} body={resp.text[:300]}", flush=True)
        if resp.status_code < 400:
            print(f"[Wasender] OTP delivered to {phone}", flush=True)
            return True
        else:
            print(f"[Wasender] Message returned failure for {phone}", flush=True)
            return False
    except Exception as e:
        print(f"[Wasender ERROR] {type(e).__name__}: {e}", flush=True)
        return False

