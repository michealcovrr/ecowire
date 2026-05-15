import uuid
import hmac
import hashlib
import httpx
from app.config import get_settings

settings = get_settings()


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.squad_secret_key}",
        "Content-Type": "application/json",
    }


def _idempotency_key(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    computed = (
        hmac.new(settings.squad_secret_key.encode(), raw_body, hashlib.sha512)
        .hexdigest()
        .upper()
    )
    return hmac.compare_digest(computed, signature.upper())


async def create_virtual_account(
    customer_identifier: str,
    first_name: str,
    last_name: str,
    mobile_num: str,
    email: str,
    bvn: str,
    dob: str,
    address: str,
    gender: str = "1",
) -> dict:
    payload = {
        "customer_identifier": customer_identifier,
        "first_name": first_name,
        "last_name": last_name,
        "mobile_num": mobile_num,
        "email": email,
        "bvn": bvn,
        "dob": dob,
        "address": address,
        "gender": gender,
        # 10-digit settlement account. In sandbox we use a placeholder;
        # production should be the merchant's configured settlement account.
        "beneficiary_account": "0000000000",
    }
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.post(
            f"{settings.squad_base_url}/virtual-account",
            json=payload,
            headers=_headers(),
            timeout=30,
        )
        print(f"[Squad VA] status={resp.status_code} body={resp.text[:500]}", flush=True)
        resp.raise_for_status()
        return resp.json()


async def create_dynamic_virtual_account(
    transaction_ref: str,
    amount: int,
    duration_minutes: int = 2880,  # 48 hours
) -> dict:
    payload = {
        "transaction_ref": transaction_ref,
        "amount": amount,
        "duration": duration_minutes,
    }
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.post(
            f"{settings.squad_base_url}/virtual-account/create-dynamic-virtual-account",
            json=payload,
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


async def transfer(
    account_number: str,
    bank_code: str,
    account_name: str,
    amount: int,           # in kobo
    narration: str,
    transaction_ref: str | None = None,
    currency_id: str = "NGN",
) -> dict:
    ref = transaction_ref or _idempotency_key("txn")
    payload = {
        "account_number": account_number,
        "bank_code": bank_code,
        "account_name": account_name,
        "amount": amount,
        "narration": narration,
        "transaction_reference": ref,
        "currency_id": currency_id,
    }
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.post(
            f"{settings.squad_base_url}/payout/transfer",
            json=payload,
            headers=_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


# CBN 3-digit code → Squad 6-digit NIP code
_NIP_CODES: dict[str, str] = {
    "058": "000013",  # GTBank
    "044": "000014",  # Access Bank
    "011": "000016",  # First Bank
    "057": "000015",  # Zenith Bank
    "033": "000004",  # UBA
    "070": "000007",  # Fidelity
    "214": "000003",  # FCMB
    "232": "000022",  # Sterling
    "032": "000018",  # Union Bank
    "010": "000010",  # Ecobank
    "035": "000017",  # Wema
    "076": "000020",  # Heritage
}


def _to_nip_code(bank_code: str) -> str:
    """Convert 3-digit CBN code to 6-digit NIP code. Pass through if already 6 digits."""
    if len(bank_code) == 6:
        return bank_code
    return _NIP_CODES.get(bank_code, bank_code.zfill(6))


async def lookup_account(account_number: str, bank_code: str) -> dict:
    payload = {"account_number": account_number, "bank_code": _to_nip_code(bank_code)}
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.post(
            f"{settings.squad_base_url}/payout/account/lookup",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


async def get_transactions(customer_identifier: str) -> dict:
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.get(
            f"{settings.squad_base_url}/virtual-account/customer/transactions/{customer_identifier}",
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


async def get_wallet_balance() -> dict:
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.get(
            f"{settings.squad_base_url}/merchant/balance",
            params={"currency_id": "NGN"},
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()


async def requery_transfer(transaction_ref: str) -> dict:
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.post(
            f"{settings.squad_base_url}/payout/requery",
            json={"transaction_ref": transaction_ref},
            headers=_headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
