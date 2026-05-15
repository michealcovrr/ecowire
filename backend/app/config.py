from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Squad
    squad_secret_key: str = ""
    squad_public_key: str = ""
    squad_base_url: str = "https://sandbox-api-d.squadco.com"

    # Dojah (kept for reference, not used)
    dojah_app_id: str = ""
    dojah_private_key: str = ""
    dojah_base_url: str = "https://api.dojah.io"

    # Prembly KYC (prembly.com — secret key + public key, no App ID needed)
    prembly_api_key: str = ""       # test_sk_... or live_sk_...
    prembly_public_key: str = ""    # test_pk_... or live_pk_... (used as app-id header)
    prembly_app_id: str = ""        # leave blank — derived from public key if not set
    prembly_sandbox: bool = True
    kyc_mock: bool = False   # bypass Prembly entirely; accepts any 11-digit number

    # Termii (kept for reference, replaced by Africa's Talking)
    termii_api_key: str = ""
    termii_sender_id: str = "alwi"
    termii_base_url: str = "https://v3.api.termii.com"



    # Wasender WhatsApp
    wasender_api_keys: str = ""
    wasender_api_url: str = "https://www.wasenderapi.com/api/send-message"

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # AI
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/econet"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # App
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 10080  # 7 days

    # Encryption key for KYC values at rest (Fernet key)
    encryption_key: str = ""

    ml_service_url: str = "http://localhost:8001"
    frontend_url: str = "http://localhost:3000"

    # OTP
    otp_expiry_seconds: int = 300
    otp_max_attempts: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
