import random
import httpx
import redis.asyncio as aioredis
from app.config import get_settings

settings = get_settings()

_redis: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        kwargs: dict = {"decode_responses": True}
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

    attempts = await r.get(_attempts_key(normalised))
    if attempts and int(attempts) >= settings.otp_max_attempts:
        return False

    otp = _generate_otp()
    print(f"[send_otp] storing otp={otp} key={_otp_key(normalised)} ttl={settings.otp_expiry_seconds}", flush=True)
    await r.setex(_otp_key(normalised), settings.otp_expiry_seconds, otp)
    check = await r.get(_otp_key(normalised))
    check_ttl = await r.ttl(_otp_key(normalised))
    print(f"[send_otp] verified after setex: stored={check} ttl={check_ttl}", flush=True)

    pipe = r.pipeline()
    pipe.incr(_attempts_key(normalised))
    pipe.expire(_attempts_key(normalised), 3600)
    await pipe.execute()

    await _dispatch_sms(normalised, otp)
    print(f"\n{'='*50}\n[DEV] OTP for {normalised}: {otp}\n{'='*50}\n", flush=True)
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

    # Wati WhatsApp takes priority (template message — no prior session needed)
    if settings.wati_api_url and settings.wati_token:
        await _dispatch_wati(phone, otp)
    elif settings.at_api_key:
        await _dispatch_at_sms(to, f"Your EcoNet code is {otp}. Valid for 5 minutes. Do not share.")
    else:
        print("[DEV] No delivery channel configured — OTP printed above only", flush=True)


async def _dispatch_wati(phone: str, otp: str) -> None:
    message = f"Your EcoNet verification code is {otp}. Valid for 10 minutes. Do not share."
    headers = {
        "Authorization": f"Bearer {settings.wati_token}",
        "Content-Type": "application/json",
    }

    # Ensure contact exists in Wati (required before session message can be sent)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            await client.post(
                f"{settings.wati_api_url}/api/v1/addContact/{phone}",
                headers=headers,
            )
    except Exception:
        pass  # Non-fatal — contact may already exist

    # Step 1: session message (works when contact has messaged the bot within 24h)
    session_delivered = False
    try:
        session_url = f"{settings.wati_api_url}/api/v1/sendSessionMessage/{phone}"
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.post(session_url, params={"messageText": message}, headers=headers)
        print(f"[Wati session] status={resp.status_code} body={resp.text[:300]}", flush=True)
        try:
            body_json = resp.json()
            session_delivered = bool(body_json.get("result"))
        except Exception:
            session_delivered = resp.status_code < 400
    except Exception as e:
        print(f"[Wati session ERROR] {type(e).__name__}: {e}", flush=True)

    if session_delivered:
        print(f"[Wati] OTP delivered via session message to {phone}", flush=True)
        return

    # Step 2: template fallback (requires APPROVED template in Wati dashboard)
    if not settings.wati_otp_template:
        print("[Wati] No approved template — OTP only in server logs.", flush=True)
        return

    print(f"[Wati] Trying template '{settings.wati_otp_template}'...", flush=True)
    try:
        payload = {
            "template_name": settings.wati_otp_template,
            "broadcast_name": f"otp_{phone[-6:]}",
            "parameters": [{"name": "1", "value": otp}],
        }
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.post(
                f"{settings.wati_api_url}/api/v1/sendTemplateMessage",
                json=payload,
                params={"whatsappNumber": phone},
                headers=headers,
            )
        print(f"[Wati template] status={resp.status_code} body={resp.text}", flush=True)
    except Exception as e:
        print(f"[Wati template ERROR] {type(e).__name__}: {e}", flush=True)


async def _dispatch_at_sms(to: str, message: str) -> None:
    form_data = {
        "username": settings.at_username,
        "to": to,
        "message": message,
    }
    if settings.at_sender_id:
        form_data["from"] = settings.at_sender_id

    try:
        async with httpx.AsyncClient(verify=False, timeout=15) as client:
            resp = await client.post(
                settings.at_sms_url,
                data=form_data,
                headers={
                    "apiKey": settings.at_api_key,
                    "Accept": "application/json",
                },
            )
            print(f"[AT SMS] status={resp.status_code} body={resp.text}", flush=True)
    except Exception as e:
        print(f"[AT SMS ERROR] {type(e).__name__}: {e}", flush=True)
