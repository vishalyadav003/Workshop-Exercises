"""Flask web interface for the Campus Event Registration Workflow Simulator."""
import csv
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_file

from utils import DATA_FILE, LOG_FILE, get_logger, validate_email, validate_identifier, validate_text

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
logger = get_logger()
DATA_DIR = Path(DATA_FILE).parent
EVENTS_FILE = DATA_DIR / "events.json"
REGISTRATIONS_FILE = DATA_DIR / "registrations.json"
CSV_FILE = DATA_DIR / "attendance.csv"


def save_json(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            import json
            json.dump(rows, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def load_json(path):
    import json
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        rows = json.load(stream)
    if not isinstance(rows, list):
        raise ValueError(f"{path.name} must contain a JSON array")
    return rows


def ensure_data_files():
    """Split legacy combined data on first use, preserving its sample records."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if EVENTS_FILE.exists() and REGISTRATIONS_FILE.exists():
        return
    legacy = {}
    if DATA_FILE.exists():
        import json
        with DATA_FILE.open(encoding="utf-8") as stream:
            legacy = json.load(stream)
    if isinstance(legacy, list):
        legacy_events, legacy_registrations = [], legacy
    elif isinstance(legacy, dict):
        legacy_events = legacy.get("events", [])
        legacy_registrations = legacy.get("registrations", [])
    else:
        raise ValueError("Legacy registrations.json must contain an object or array")
    if not EVENTS_FILE.exists():
        save_json(EVENTS_FILE, legacy_events)
    if not REGISTRATIONS_FILE.exists():
        save_json(REGISTRATIONS_FILE, legacy_registrations)


def read_store():
    ensure_data_files()
    return load_json(EVENTS_FILE), load_json(REGISTRATIONS_FILE)


def dashboard_state():
    events, registrations = read_store()
    counts = {event["event_id"].casefold(): 0 for event in events}
    for registration in registrations:
        key = registration.get("event_id", "").casefold()
        if key in counts:
            counts[key] += 1
    event_rows = []
    for event in events:
        registered = counts.get(event["event_id"].casefold(), 0)
        event_rows.append({**event, "registered": registered,
                           "available": max(0, event["capacity"] - registered)})
    names = {event["event_id"].casefold(): event["name"] for event in event_rows}
    registrations = [
        {**row, "event_name": names.get(row.get("event_id", "").casefold(), "[unknown event]")}
        for row in registrations
    ]
    return {
        "events": event_rows,
        "registrations": registrations,
        "summary": {
            "events": len(event_rows),
            "registrations": len(registrations),
            "available_seats": sum(event["available"] for event in event_rows),
            "capacity": sum(event["capacity"] for event in event_rows),
            "utilization": round((sum(event["registered"] for event in event_rows) / sum(event["capacity"] for event in event_rows)) * 100) if sum(event["capacity"] for event in event_rows) else 0,
        },
    }


def error_response(error, status=400):
    logger.warning("WEB_REQUEST_FAILED path=%s reason=%s", request.path, error)
    return jsonify(error=str(error)), status


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/events")
def events_page():
    # Keep one live, interactive catalogue so actions work the same from every entry point.
    return redirect("/#events")


@app.get("/api/activity")
def activity():
    try:
        if not LOG_FILE.exists():
            return jsonify(entries=[])
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()[-100:]
        return jsonify(entries=list(reversed(lines)))
    except OSError as exc:
        return error_response(exc, 500)


@app.get("/api/state")
def get_state():
    try:
        return jsonify(dashboard_state())
    except (ValueError, OSError) as exc:
        return error_response(exc, 500)


@app.post("/api/events")
def create_event():
    payload = request.get_json(silent=True) or {}
    try:
        event_id = validate_identifier(payload.get("event_id", ""), "Event ID")
        name = validate_text(payload.get("name", ""), "Event name")
        capacity = int(payload.get("capacity", ""))
        if capacity <= 0:
            raise ValueError("Capacity must be a positive whole number")
        events, _ = read_store()
        if any(row["event_id"].casefold() == event_id.casefold() for row in events):
            raise ValueError("Event ID already exists")
        events.append({"event_id": event_id, "name": name, "capacity": capacity})
        save_json(EVENTS_FILE, events)
        logger.info("EVENT_CREATED event_id=%s capacity=%s", event_id, capacity)
        return jsonify(message="Event created successfully.", state=dashboard_state()), 201
    except (ValueError, OSError) as exc:
        return error_response(exc)


@app.post("/api/registrations")
def create_registration():
    payload = request.get_json(silent=True) or {}
    try:
        participant_id = validate_identifier(payload.get("participant_id", ""), "Participant ID")
        name = validate_text(payload.get("name", ""), "Participant name")
        email = validate_email(payload.get("email", ""))
        event_id = validate_identifier(payload.get("event_id", ""), "Event ID")
        events, registrations = read_store()
        event = next((row for row in events if row["event_id"].casefold() == event_id.casefold()), None)
        if event is None:
            raise ValueError("Event not found")
        registered_count = sum(row["event_id"].casefold() == event_id.casefold() for row in registrations)
        if any(row["participant_id"].casefold() == participant_id.casefold()
               and row["event_id"].casefold() == event_id.casefold() for row in registrations):
            raise ValueError("Participant is already registered for this event")
        if registered_count >= event["capacity"]:
            raise ValueError("Event is full; no seats are available")
        registrations.append({"participant_id": participant_id, "name": name, "email": email,
                              "event_id": event["event_id"],
                              "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
        save_json(REGISTRATIONS_FILE, registrations)
        logger.info("REGISTRATION_SUCCESS participant_id=%s event_id=%s", participant_id, event_id)
        return jsonify(message="Registration confirmed. You’re on the list.",
                       state=dashboard_state()), 201
    except (ValueError, OSError) as exc:
        return error_response(exc)


@app.delete("/api/registrations/<participant_id>/<event_id>")
def delete_registration(participant_id, event_id):
    try:
        participant_id = validate_identifier(participant_id, "Participant ID")
        event_id = validate_identifier(event_id, "Event ID")
        _, registrations = read_store()
        remaining = [row for row in registrations if not (
            row["participant_id"].casefold() == participant_id.casefold()
            and row["event_id"].casefold() == event_id.casefold())]
        if len(remaining) == len(registrations):
            raise ValueError("Registration not found")
        save_json(REGISTRATIONS_FILE, remaining)
        logger.info("CANCELLATION_SUCCESS participant_id=%s event_id=%s", participant_id, event_id)
        return jsonify(message="Registration cancelled. The seat is available again.",
                       state=dashboard_state())
    except (ValueError, OSError) as exc:
        return error_response(exc)


@app.get("/api/export")
def export_attendance():
    try:
        events, registrations = read_store()
        names = {event["event_id"]: event["name"] for event in events}
        CSV_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CSV_FILE.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Participant ID", "Name", "Email", "Event ID", "Event Name", "Registered At (UTC)"])
            for row in registrations:
                writer.writerow([row.get("participant_id", ""), row.get("name", ""), row.get("email", ""),
                                 row.get("event_id", ""), names.get(row.get("event_id"), "[unknown event]"),
                                 row.get("registered_at", "")])
        return send_file(CSV_FILE, mimetype="text/csv; charset=utf-8",
                         as_attachment=True, download_name="attendance.csv")
    except (ValueError, OSError) as exc:
        return error_response(exc, 500)


if __name__ == "__main__":
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5101")), debug=False)
