import os
import re
import random
import httpx
from app.config import get_settings

settings = get_settings()


def _is_mock() -> bool:
    return os.getenv("KYC_MOCK", "false").lower() in ("true", "1", "yes")

_PREMBLY_BASE = "https://api.prembly.com/identitypass/verification"

# Mock data pools for demo/dev mode
_FIRST_NAMES = ["Chukwuemeka", "Adebayo", "Fatimah", "Ngozi", "Oluwaseun",
                "Amina", "Emeka", "Taiwo", "Blessing", "Ifeanyi",
                "Chiamaka", "Olumide", "Aisha", "Chidi", "Yetunde"]
_LAST_NAMES  = ["Okonkwo", "Adeyemi", "Ibrahim", "Nwosu", "Babatunde",
                "Eze", "Abubakar", "Ogundimu", "Okeke", "Lawal",
                "Musa", "Adesanya", "Obi", "Adeleke", "Bello"]


def _headers() -> dict:
    app_id = settings.prembly_app_id or settings.prembly_public_key
    return {
        "x-api-key": settings.prembly_api_key,
        "app-id": app_id,
        "Content-Type": "application/json",
    }


def _validate_bvn(bvn: str) -> None:
    if _is_mock():
        if not bvn.isdigit() or len(bvn) < 4:
            raise ValueError("Demo BVN must be at least 4 digits")
        return
    if not re.match(r"^\d{11}$", bvn):
        raise ValueError("BVN must be exactly 11 digits")


def _validate_nin(nin: str) -> None:
    if _is_mock():
        if not nin.isdigit() or len(nin) < 4:
            raise ValueError("Demo NIN must be at least 4 digits")
        return
    if not re.match(r"^\d{11}$", nin):
        raise ValueError("NIN must be exactly 11 digits")


def _mock_entity(id_value: str) -> dict:
    """Deterministic-ish fake Nigerian identity seeded from the ID digits."""
    seed = sum(int(c) for c in id_value)
    first = _FIRST_NAMES[seed % len(_FIRST_NAMES)]
    last  = _LAST_NAMES[(seed * 7) % len(_LAST_NAMES)]
    year  = 1980 + (seed % 30)
    month = 1 + (seed % 12)
    day   = 1 + (seed % 28)
    gender = "F" if (seed % 3 == 0) else "M"
    return {
        "entity": {
            "first_name": first,
            "last_name": last,
            "middle_name": "",
            "phone": "",
            "date_of_birth": f"{year}-{month:02d}-{day:02d}",
            "address": "Lagos, Nigeria",
            "gender": gender,
            "reference": f"MOCK-{id_value[-6:]}",
        }
    }


async def verify_bvn(bvn: str, phone: str) -> dict:
    _validate_bvn(bvn)

    if _is_mock():
        print(f"[KYC MOCK] BVN {bvn[:4]}****{bvn[-3:]} accepted", flush=True)
        return _mock_entity(bvn)

    async with httpx.AsyncClient(verify=False, timeout=20) as client:
        for endpoint in ["/bvn", "/bvn/advance"]:
            resp = await client.post(
                f"{_PREMBLY_BASE}{endpoint}",
                json={"number": bvn},
                headers=_headers(),
            )
            print(f"[Prembly BVN {endpoint}] status={resp.status_code} body={resp.text[:300]}", flush=True)
            if resp.status_code < 400:
                body = resp.json()
                if body.get("status"):
                    return _normalise_bvn(body)
        resp.raise_for_status()

    return _normalise_bvn(resp.json())


async def verify_nin(nin: str) -> dict:
    _validate_nin(nin)

    if _is_mock():
        print(f"[KYC MOCK] NIN {nin[:4]}****{nin[-3:]} accepted", flush=True)
        return _mock_entity(nin)

    async with httpx.AsyncClient(verify=False, timeout=20) as client:
        resp = await client.post(
            f"{_PREMBLY_BASE}/nin/advance",
            json={"number": nin},
            headers=_headers(),
        )
        resp.raise_for_status()

    return _normalise_nin(resp.json())


def _normalise_bvn(raw: dict) -> dict:
    bvn_data = raw.get("bvn_data") or raw.get("data") or {}
    return {
        "entity": {
            "first_name":    (bvn_data.get("firstName") or bvn_data.get("first_name") or "").strip().title(),
            "last_name":     (bvn_data.get("lastName")  or bvn_data.get("last_name")  or "").strip().title(),
            "middle_name":   (bvn_data.get("middleName") or bvn_data.get("middle_name") or "").strip().title(),
            "phone":         bvn_data.get("phoneNumber") or bvn_data.get("phone_number") or "",
            "date_of_birth": bvn_data.get("dateOfBirth") or bvn_data.get("date_of_birth") or "",
            "address":       bvn_data.get("residentialAddress") or bvn_data.get("address") or "",
            "gender":        (bvn_data.get("gender") or "M")[:1].upper(),
            "reference":     raw.get("reference") or raw.get("requestId") or "",
        }
    }


def _normalise_nin(raw: dict) -> dict:
    nin_data = raw.get("nin_data") or raw.get("data") or {}
    return {
        "entity": {
            "first_name":    (nin_data.get("firstname") or nin_data.get("first_name") or "").strip().title(),
            "last_name":     (nin_data.get("surname")   or nin_data.get("last_name")  or "").strip().title(),
            "middle_name":   (nin_data.get("middlename") or nin_data.get("middle_name") or "").strip().title(),
            "phone":         nin_data.get("phone") or "",
            "date_of_birth": nin_data.get("birthdate") or nin_data.get("date_of_birth") or "",
            "reference":     raw.get("reference") or raw.get("requestId") or "",
        }
    }
