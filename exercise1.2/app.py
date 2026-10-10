"""Flask web interface for the Exercise 1.2 library booking simulator."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import os
import uuid

from flask import Flask, jsonify, render_template, request, send_file

from main import seed_resources
from models import Booking, WaitlistEntry, overlaps, parse_day, validate_booking
from storage import DATA_DIR, load_store, save_store
from utils import export_daily_schedule, save_usage_report, usage_report

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)


def get_store():
    store, warning = load_store()
    before = bool(store["resources"])
    seed_resources(store)
    if not before:
        save_store(store)
    return store, warning


def snapshot(day: str | None = None):
    store, warning = get_store()
    selected = parse_day(day).isoformat() if day else date.today().isoformat()
    active = [b for b in store["bookings"] if b.status == "active"]
    resources = []
    now = datetime.now().strftime("%H:%M")
    for resource in store["resources"]:
        bookings = [b for b in active if b.resource_id == resource.resource_id and b.booking_date == selected]
        occupied_now = selected == date.today().isoformat() and any(b.start_time <= now < b.end_time for b in bookings)
        resources.append({**resource.__dict__, "day_booking_count": len(bookings), "occupied_now": occupied_now})
    top = sorted(store["resources"], key=lambda r: (-sum(b.resource_id == r.resource_id for b in active), r.resource_id))
    return {
        "resources": resources,
        "bookings": [b.__dict__ for b in store["bookings"]],
        "waitlist": [w.__dict__ for w in store["waitlist"]],
        "summary": {"total_resources": len(resources), "active_bookings": len(active),
                    "available_resources": sum(r.available for r in store["resources"]),
                    "cancelled_bookings": sum(b.status == "cancelled" for b in store["bookings"]),
                    "waitlist_count": len(store["waitlist"]),
                    "top_resources": [{"resource_id": r.resource_id, "count": sum(b.resource_id == r.resource_id for b in active)} for r in top[:3]]},
        "selected_date": selected, "warning": warning,
    }


@app.get("/")
def index():
    return render_template("index.html", today=date.today().isoformat(), page="overview")


@app.get("/schedule")
def schedule_page():
    return render_template("schedule.html", today=date.today().isoformat(), page="schedule")


@app.get("/api/state")
def state():
    try:
        return jsonify(snapshot(request.args.get("date")))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.get("/api/export")
def export():
    try:
        day = parse_day(request.args.get("date", "")).isoformat()
        store, _ = get_store()
        path = export_daily_schedule(store["bookings"], day, DATA_DIR)
        return send_file(path, as_attachment=True, download_name=path.name, mimetype="text/csv")
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.post("/api/bookings")
def create_booking():
    payload = request.get_json(silent=True) or {}
    try:
        store, _ = get_store()
        rid, user = str(payload.get("resource_id", "")).strip(), str(payload.get("user_id", "")).strip()
        if not user:
            raise ValueError("Enter your user ID to continue.")
        resource = next((r for r in store["resources"] if r.resource_id.lower() == rid.lower()), None)
        if resource is None:
            raise ValueError("Choose a resource from the catalogue.")
        if not resource.available:
            raise ValueError("This resource is under maintenance and cannot be booked.")
        day, start, end = validate_booking(str(payload.get("date", "")), str(payload.get("start_time", "")), str(payload.get("end_time", "")))
        s, e = start.strftime("%H:%M"), end.strftime("%H:%M")
        conflict = next((b for b in store["bookings"] if b.status == "active" and b.resource_id == rid and b.booking_date == day.isoformat() and overlaps(s, e, b.start_time, b.end_time)), None)
        if conflict:
            if not payload.get("join_waitlist"):
                return jsonify(error=f"That slot conflicts with {conflict.start_time}–{conflict.end_time} (booking {conflict.booking_id}).", conflict=True), 409
            entry = WaitlistEntry(uuid.uuid4().hex[:12], resource.resource_id, user, day.isoformat(), s, e, datetime.now().isoformat(timespec="seconds"))
            store["waitlist"].append(entry)
            save_store(store)
            return jsonify(message="Added to the wait-list for that time slot.", waitlisted=True, state=snapshot(day.isoformat())), 201
        booking = Booking.create(resource.resource_id, user, day, start, end)
        store["bookings"].append(booking)
        save_store(store)
        return jsonify(message=f"Booking confirmed. Your reference is {booking.booking_id}.", booking=booking.__dict__, state=snapshot(day.isoformat())), 201
    except (ValueError, KeyError, TypeError) as exc:
        return jsonify(error=str(exc)), 400
    except OSError as exc:
        return jsonify(error=f"Could not save the change: {exc}"), 500


@app.post("/api/cancel")
def cancel_booking():
    payload = request.get_json(silent=True) or {}
    try:
        store, _ = get_store()
        key = str(payload.get("booking_id", "")).strip().lower()
        booking = next((b for b in store["bookings"] if b.booking_id.lower() == key and b.status == "active"), None)
        if booking is None:
            raise ValueError("No active booking matches that ID.")
        booking.status = "cancelled"
        save_store(store)
        waiting = [w for w in store["waitlist"] if w.resource_id == booking.resource_id and w.booking_date == booking.booking_date and overlaps(booking.start_time, booking.end_time, w.start_time, w.end_time)]
        first = min(waiting, key=lambda w: w.created_at) if waiting else None
        message = f"Booking {booking.booking_id} cancelled."
        if first:
            message += f" Wait-list: {first.user_id} is first for an overlapping slot ({first.start_time}–{first.end_time}); staff confirmation is required."
        return jsonify(message=message, state=snapshot(booking.booking_date))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except OSError as exc:
        return jsonify(error=f"Could not save the change: {exc}"), 500


@app.post("/api/report")
def report():
    store, _ = get_store()
    result = usage_report(store["resources"], store["bookings"])
    path = save_usage_report(result, DATA_DIR)
    return jsonify(report=result, saved_to=str(path.relative_to(ROOT)))


if __name__ == "__main__":
    print("Library Resource Hub running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5102")), debug=False)
