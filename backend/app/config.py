from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)


@dataclass(frozen=True)
class Settings:
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db: str = os.getenv("MONGODB_DB", "smart_attendance")
    frontend_base_url: str = os.getenv("FRONTEND_BASE_URL", "http://localhost:8000/static")

    mail_username: str | None = os.getenv("MAIL_USERNAME")
    mail_password: str | None = os.getenv("MAIL_PASSWORD")
    mail_from: str | None = os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME"))
    mail_server: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    mail_port: int = int(os.getenv("MAIL_PORT", "587"))
    mail_starttls: bool = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
    mail_ssl_tls: bool = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"
    use_credentials: bool = os.getenv("USE_CREDENTIALS", "True").lower() == "true"
    mail_enabled: bool = os.getenv("MAIL_ENABLED", "true").lower() == "true"

    campus_lat: float = float(os.getenv("CAMPUS_LAT", "28.6139"))
    campus_lon: float = float(os.getenv("CAMPUS_LON", "77.2090"))
    max_distance_km: float = float(os.getenv("MAX_DISTANCE_KM", "3.0"))
    late_hour: int = int(os.getenv("LATE_HOUR", "9"))
    late_minute: int = int(os.getenv("LATE_MINUTE", "30"))
    absent_notice_hour: int = int(os.getenv("ABSENT_NOTICE_HOUR", "17"))
    absent_notice_minute: int = int(os.getenv("ABSENT_NOTICE_MINUTE", "0"))
    absent_notifications_enabled: bool = os.getenv("ABSENT_NOTIFICATIONS_ENABLED", "true").lower() == "true"

    face_tolerance: float = float(os.getenv("FACE_TOLERANCE", "0.5"))
    face_rec_enabled: bool = os.getenv("FACE_RECOGNITION_ENABLED", "true").lower() == "true"
    mfa_enabled: bool = os.getenv("MFA_ENABLED", "false").lower() == "true"
    geofencing_enabled: bool = os.getenv("GEOFENCING_ENABLED", "false").lower() == "true"
    lockout_enabled: bool = os.getenv("LOCKOUT_ENABLED", "false").lower() == "true"


settings = Settings()
