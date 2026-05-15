import base64
from cryptography.fernet import Fernet
from app.config import get_settings

settings = get_settings()

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.encryption_key
        if not key:
            # Dev-only fallback — deterministic key so values survive restarts
            key = base64.urlsafe_b64encode(b"econet-dev-key-do-not-use-in-prod!!").decode()
        _fernet = Fernet(key.encode())
    return _fernet


def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()
