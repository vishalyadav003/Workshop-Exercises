"""Validation, logging and persistence helpers."""
import json
import logging
import os
import re
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATA_FILE = DATA_DIR / "registrations.json"
CSV_FILE = DATA_DIR / "attendance.csv"
LOG_FILE = LOG_DIR / "app.log"

def get_logger():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("campus_registration")
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

def validate_identifier(value, label="ID"):
    value = value.strip() if isinstance(value, str) else ""
    if not value or len(value) > 40 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise ValueError(f"{label} must be 1-40 characters: letters, numbers, dot, underscore or hyphen")
    return value

def validate_text(value, label, max_length=120):
    value = value.strip() if isinstance(value, str) else ""
    if not value or len(value) > max_length or any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{label} is required and must be at most {max_length} characters")
    return value

def validate_email(value):
    value = value.strip() if isinstance(value, str) else ""
    pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
    if len(value) > 254 or not re.fullmatch(pattern, value):
        raise ValueError("Enter a valid email address with a domain")
    return value

def load_data(path=DATA_FILE):
    """Load and validate the JSON document; never overwrite malformed data."""
    path = Path(path)
    if not path.exists():
        return {"events": [], "registrations": []}
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, dict) or not isinstance(data.get("events"), list) or not isinstance(data.get("registrations"), list):
            raise ValueError("expected events and registrations arrays")
        return data
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        get_logger().exception("DATA_LOAD_FAILED path=%s", path)
        raise ValueError(f"Cannot read data file {path}: {exc}. Repair or restore the file before continuing.") from exc

def save_data(data, path=DATA_FILE):
    """Atomically replace JSON to avoid leaving a partially-written file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
