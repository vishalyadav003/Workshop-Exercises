"""Small JSON-backed persistence layer for notices."""
import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = ("Electronics", "Bags & Accessories", "Clothing", "ID & Cards", "Keys", "Books & Stationery", "Other")
ZONES = ("Library", "Academic Block", "Cafeteria", "Sports Complex", "Hostels", "Main Gate", "Other")
KINDS = ("Lost", "Found")
MAX_DESCRIPTION = 1000
_lock = threading.RLock()


def _path(path=None):
    if path:
        return Path(path)
    from flask import current_app
    return Path(current_app.config["DATA_FILE"])


def all_notices(path=None):
    file_path = _path(path)
    try:
        with _lock:
            return json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def get_notice(notice_id, path=None):
    return next((n for n in all_notices(path) if n["id"] == notice_id), None)


def save_notices(notices, path=None):
    file_path = _path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        fd, temp_name = tempfile.mkstemp(dir=file_path.parent, prefix="notices-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(notices, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, file_path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def create_notice(values, path=None):
    record = {
        "id": uuid.uuid4().hex,
        "kind": values["kind"],
        "category": values["category"],
        "description": values["description"],
        "zone": values["zone"],
        "event_date": values["event_date"],
        "contact": values["contact"],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "resolved": False,
    }
    notices = all_notices(path)
    notices.insert(0, record)
    save_notices(notices, path)
    return record


def resolve_notice(notice_id, path=None):
    notices = all_notices(path)
    for notice in notices:
        if notice["id"] == notice_id:
            notice["resolved"] = True
            save_notices(notices, path)
            return notice
    return None
