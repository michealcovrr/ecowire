import re
import httpx
from app.config import get_settings

settings = get_settings()

# Realistic mock identities for demo/sandbox use when Dojah is not configured.
# Keyed by BVN/NIN value so the same input always returns the same name.
_MOCK_IDENTITIES = {
    "22222222222": {"first_name": "Chukwuemeka", "last_name": "Okonkwo", "middle_name": "Tunde"},
    "11111111111": {"first_name": "Ngozi",       "last_name": "Adeyemi",  "middle_name": "Chioma"},
    "33333333333": {"first_name": "Musa",         "last_name": "Ibrahim",  "middle_name": "Abubakar"},
    "44444444444": {"first_name": "Amaka",        "last_name": "Nwosu",    "middle_name": "Grace"},
    "55555555555": {"first_name": "Biodun",       "last_name": "Olatunji", "middle_name": "Segun"},
}
_MOCK_DEFAULT = {"first_name": "alwi", "last_name": "User", "middle_name": ""}


def _mock_response(kyc_value: str, kyc_type: str) -> dict:
    identity = _MOCK_IDENTITIES.get(kyc_value, _MOCK_DEFAULT)
    return {
        "entity": {
            **identity,
            kyc_type.lower(): kyc_value,
            "phone": "",
            "date_of_birth": "1990-01-01",
        }
    }


def _is_configured() -> bool:
    return bool(settings.dojah_app_id and settings.dojah_private_key)


def _headers() -> dict:
    return {
        "AppId": settings.dojah_app_id,
        "Authorization": settings.dojah_private_key,
        "Content-Type": "application/json",
    }


def _validate_bvn(bvn: str) -> None:
    if not re.match(r"^\d{11}$", bvn):
        raise ValueError("BVN must be exactly 11 digits")


def _validate_nin(nin: str) -> None:
    if not re.match(r"^\d{11}$", nin):
        raise ValueError("NIN must be exactly 11 digits")


async def verify_bvn(bvn: str, phone: str) -> dict:
    """
    Validates a BVN. Calls Dojah when credentials are configured,
    otherwise returns a realistic mock response for dev/demo use.
    Never log the raw BVN — log only the reference ID returned.
    """
    _validate_bvn(bvn)

    if not _is_configured():
        return _mock_response(bvn, "BVN")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.dojah_base_url}/api/v1/kyc/bvn",
            params={"bvn": bvn},
            headers=_headers(),
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()


async def verify_nin(nin: str) -> dict:
    """
    Validates a NIN. Calls Dojah when credentials are configured,
    otherwise returns a realistic mock response for dev/demo use.
    Never log the raw NIN — log only the reference ID returned.
    """
    _validate_nin(nin)

    if not _is_configured():
        return _mock_response(nin, "NIN")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.dojah_base_url}/api/v1/kyc/nin",
            params={"nin": nin},
            headers=_headers(),
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()


async def verify_liveness(image_url: str, bvn: str) -> dict:
    """Tier 3 liveness check — required for loans and insurance."""
    if not _is_configured():
        return {"entity": {"match": True, "confidence": 0.95}}

    payload = {"selfie_image": image_url, "bvn": bvn}
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.dojah_base_url}/api/v1/kyc/selfie/verify",
            json=payload,
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
