"""Web server configuration for BookEase public portal."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class WebConfig:
    SECRET_KEY = os.environ.get("BOOKEASE_SECRET_KEY", "bookease-dev-secret-change-in-production")
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV", "development") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600 * 8  # 8 hours
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
    WEB_HOST = os.environ.get("HOST", "0.0.0.0")
    WEB_PORT = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("FLASK_ENV", "development") == "development"
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"
    RATELIMIT_BOOKING = "5 per minute;20 per hour"
