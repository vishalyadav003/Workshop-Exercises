"""JSON persistence with validation and recoverable fallback behavior."""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Any
from models import Resource, Booking, WaitlistEntry, resource_from_dict, booking_from_dict

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_FILE = DATA_DIR / "bookings.json"

def empty_store() -> dict[str, list]:
    return {"resources": [], "bookings": [], "waitlist": []}

def _validate(raw: Any) -> dict[str, list]:
    if not isinstance(raw, dict):
        raise ValueError("Root JSON must be an object")
    if not raw:
        return empty_store()
    resources = [resource_from_dict(x) for x in raw.get("resources", [])]
    bookings = [booking_from_dict(x) for x in raw.get("bookings", [])]
    waitlist = []
    for x in raw.get("waitlist", []):
        if not isinstance(x, dict): raise ValueError("Invalid wait-list record")
        for key in ("waitlist_id", "resource_id", "user_id", "booking_date", "start_time", "end_time"):
            if not x.get(key): raise ValueError("Incomplete wait-list record")
        waitlist.append(WaitlistEntry(x["waitlist_id"], x["resource_id"], x["user_id"], x["booking_date"], x["start_time"], x["end_time"], x.get("created_at", "")))
    ids = [r.resource_id for r in resources]
    if len(ids) != len(set(ids)): raise ValueError("Duplicate resource IDs")
    known = set(ids)
    if any(b.resource_id not in known for b in bookings) or any(w.resource_id not in known for w in waitlist):
        raise ValueError("Booking or wait-list item refers to an unknown resource")
    # Prevent malformed or conflicting active records from poisoning future operations.
    active = [b for b in bookings if b.status == "active"]
    for i, left in enumerate(active):
        for right in active[i+1:]:
            if left.resource_id == right.resource_id and left.booking_date == right.booking_date:
                from models import overlaps
                if overlaps(left.start_time, left.end_time, right.start_time, right.end_time):
                    raise ValueError("Overlapping active bookings in data")
    return {"resources": resources, "bookings": bookings, "waitlist": waitlist}

def load_store(path: Path = DATA_FILE) -> tuple[dict[str, list], str | None]:
    """Load data; missing/empty files initialize cleanly, invalid files are backed up."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists(): return empty_store(), "Data file missing; initialized an empty catalogue."
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip(): return empty_store(), "Data file was empty; initialized an empty catalogue."
        raw = json.loads(text)
        return _validate(raw), None
    except (json.JSONDecodeError, ValueError, TypeError, KeyError, OSError) as exc:
        backup = path.with_name(path.name + ".corrupt")
        try: shutil.copy2(path, backup)
        except OSError: backup = None
        message = f"Data file was invalid ({exc}); initialized an empty catalogue."
        if backup: message += f" Original copied to {backup.name}."
        return empty_store(), message

def save_store(store: dict[str, list], path: Path = DATA_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = {key: [item.__dict__ if hasattr(item, "__dict__") else item for item in values]
                    for key, values in store.items()}
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(serializable, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)
