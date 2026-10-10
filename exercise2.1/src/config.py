"""Load and validate application configuration without exposing secret values."""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Mapping, Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_name: str
    api_token: str
    log_level: str


def load_settings(env_file: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> Settings:
    """Load settings; process environment takes precedence over the optional dotenv file."""
    if environ is None:
        load_dotenv(dotenv_path=env_file or PROJECT_ROOT / ".env", override=False)
        values = os.environ
    else:
        values = environ
    return Settings(
        app_env=values.get("APP_ENV", "development").strip(),
        app_name=values.get("APP_NAME", "exercise2.1").strip(),
        api_token=values.get("API_TOKEN", "").strip(),
        log_level=values.get("LOG_LEVEL", "INFO").strip().upper(),
    )


def validate_settings(settings: Settings) -> list[str]:
    """Return safe, value-free configuration errors."""
    errors = []
    if not settings.app_env:
        errors.append("APP_ENV must not be empty")
    if not settings.app_name:
        errors.append("APP_NAME must not be empty")
    if not settings.api_token or settings.api_token == "replace-with-a-local-placeholder":
        errors.append("API_TOKEN is missing or still contains the example placeholder")
    if settings.log_level not in {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}:
        errors.append("LOG_LEVEL must be one of CRITICAL, ERROR, WARNING, INFO, DEBUG")
    return errors
