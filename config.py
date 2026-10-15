"""Application configuration.

Values are read from environment variables (optionally loaded from a local
``.env`` file) so that no production secret is ever hard-coded.
"""

from __future__ import annotations

import os
import secrets

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean flag from the environment."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    """Base configuration shared by every environment."""

    # A random per-process key is used when SECRET_KEY is not provided. This is
    # safe for local development (sessions/CSRF tokens simply reset on restart)
    # but ProductionConfig refuses to start without an explicit key.
    SECRET_KEY: str = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

    FLASK_ENV: str = os.environ.get("FLASK_ENV", "production")
    DEBUG: bool = False
    TESTING: bool = False

    # Reject request bodies larger than 16 KiB. Password analysis and
    # generation requests are tiny, so anything bigger is abuse.
    MAX_CONTENT_LENGTH: int = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024))

    # CSRF protection (Flask-WTF). The API reads the token from a header.
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int | None = None  # token lives as long as the browser session
    WTF_CSRF_HEADERS: list[str] = ["X-CSRFToken", "X-CSRF-Token"]

    # Session cookie hardening (the session only carries the CSRF token).
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Strict"
    SESSION_COOKIE_SECURE: bool = _env_bool("SESSION_COOKIE_SECURE", False)

    # Input limits.
    MAX_PASSWORD_LENGTH: int = 256

    # Simple in-memory rate limiting for the JSON API.
    RATE_LIMIT_ENABLED: bool = _env_bool("RATE_LIMIT_ENABLED", True)
    RATE_LIMIT_REQUESTS: int = int(os.environ.get("RATE_LIMIT_REQUESTS", 120))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", 60))

    # Static files change rarely; cache them for an hour.
    SEND_FILE_MAX_AGE_DEFAULT: int = 3600


class DevelopmentConfig(Config):
    """Local development settings."""

    FLASK_ENV = "development"
    DEBUG = True
    SEND_FILE_MAX_AGE_DEFAULT = 0


class TestingConfig(Config):
    """Settings used by the pytest suite."""

    TESTING = True
    SECRET_KEY = "testing-only-secret-key"
    WTF_CSRF_ENABLED = False
    RATE_LIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production settings. Requires SECRET_KEY to be set explicitly."""

    SESSION_COOKIE_SECURE = True

    @staticmethod
    def validate() -> None:
        """Fail fast if a production secret key was not supplied."""
        if not os.environ.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY must be set in the environment for production.")


CONFIG_BY_NAME: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config() -> type[Config]:
    """Return the configuration class selected by the FLASK_ENV variable."""
    return CONFIG_BY_NAME.get(os.environ.get("FLASK_ENV", "development"), DevelopmentConfig)
