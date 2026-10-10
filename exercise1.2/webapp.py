"""Browser dashboard for the standard-library library booking simulator."""
from __future__ import annotations

import json
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import uuid

from main import seed_resources
from models import Booking, WaitlistEntry, overlaps, validate_booking, parse_day
from storage import DATA_DIR, load_store, save_store
from utils import export_daily_schedule, save_usage_report, usage_report

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"


def snapshot(day: str | None = None) -> dict:
    store, warning = load_store()
    had_resources = bool(store["resources"])
    seed_resources(store)
    if not had_resources:
        save_store(store)
    chosen_day = parse_day(day).isoformat() if day else date.today().isoformat()
    active = [b for b in store["bookings"] if b.status == "active"]
    resources = []
    for resource in store["resources"]:
        day_bookings = [b for b in active if b.resource_id == resource.resource_id and b.booking_date == chosen_day]
        resources.append({**resource.__dict__, "day_booking_count": len(day_bookings)})
    def has_open_time(resource):
        cursor = "00:00"
        for booking in sorted((b for b in active if b.resource_id == resource.resource_id and b.booking_date == chosen_day), key=lambda b: b.start_time):
            if booking.start_time > cursor:
                return True
            cursor = max(cursor, booking.end_time)
        return cursor < "23:59"
    return {
        "resources": resources,
        "bookings": [b.__dict__ for b in store["bookings"]],
        "waitlist": [w.__dict__ for w in store["waitlist"]],
        "summary": {
            "total_resources": len(resources),
            "active_bookings": len(active),
            "available_resources": sum(r.available and has_open_time(r) for r in store["resources"]),
            "cancelled_bookings": sum(b.status == "cancelled" for b in store["bookings"]),
        },
        "selected_date": chosen_day,
        "warning": warning,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def respond(self, payload, status=200, content_type="application/json; charset=utf-8", extra_headers=None):
        data = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        size = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(size) or b"{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            try:
                self.respond(snapshot(parse_qs(parsed.query).get("date", [None])[0]))
            except ValueError as exc:
                self.respond({"error": str(exc)}, 400)
            return
        if parsed.path == "/api/export":
            try:
                day = parse_day(parse_qs(parsed.query).get("date", [""])[0]).isoformat()
                store, _ = load_store()
                path = export_daily_schedule(store["bookings"], day, DATA_DIR)
                self.respond(path.read_bytes(), content_type="text/csv; charset=utf-8",
                             extra_headers={"Content-Disposition": f'attachment; filename="{path.name}"'})
            except ValueError as exc:
                self.respond({"error": str(exc)}, 400)
            return
        if parsed.path == "/":
            path = WEB_DIR / "index.html"
        else:
            path = (WEB_DIR / parsed.path.lstrip("/")).resolve()
            if WEB_DIR.resolve() not in path.parents:
                self.respond({"error": "Not found"}, 404)
                return
        if not path.is_file():
            self.respond({"error": "Not found"}, 404)
            return
        kind = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}.get(path.suffix, "application/octet-stream")
        self.respond(path.read_bytes(), content_type=f"{kind}; charset=utf-8")

    def do_POST(self):
        try:
            payload = self.body()
            store, _ = load_store()
            seed_resources(store)
            if self.path == "/api/bookings":
                rid, user = str(payload.get("resource_id", "")).strip(), str(payload.get("user_id", "")).strip()
                if not user:
                    raise ValueError("Enter your user ID to continue.")
                resource = next((r for r in store["resources"] if r.resource_id.lower() == rid.lower()), None)
                if resource is None:
                    raise ValueError("Choose a resource from the catalogue.")
                if not resource.available:
                    raise ValueError("This resource is inactive and cannot be booked.")
                day, start, end = validate_booking(str(payload.get("date", "")), str(payload.get("start_time", "")), str(payload.get("end_time", "")))
                collision = next((b for b in store["bookings"] if b.status == "active" and b.resource_id == resource.resource_id
                                  and b.booking_date == day.isoformat() and overlaps(start.strftime("%H:%M"), end.strftime("%H:%M"), b.start_time, b.end_time)), None)
                if collision:
                    wait = WaitlistEntry(uuid.uuid4().hex[:12], resource.resource_id, user, day.isoformat(), start.strftime("%H:%M"), end.strftime("%H:%M"), datetime.now().isoformat(timespec="seconds"))
                    store["waitlist"].append(wait)
                    save_store(store)
                    self.respond({"error": f"That time conflicts with {collision.start_time}–{collision.end_time} (booking {collision.booking_id}). Your request was added to the wait-list.", "waitlisted": True, "state": snapshot(day.isoformat())}, 409)
                    return
                booking = Booking.create(resource.resource_id, user, day, start, end)
                store["bookings"].append(booking)
                save_store(store)
                self.respond({"message": f"Booking confirmed. Your reference is {booking.booking_id}.", "booking": booking.__dict__, "state": snapshot(day.isoformat())}, 201)
                return
            if self.path == "/api/cancel":
                key = str(payload.get("booking_id", "")).strip().lower()
                item = next((b for b in store["bookings"] if b.booking_id.lower() == key and b.status == "active"), None)
                if item is None:
                    raise ValueError("No active booking matches that ID.")
                item.status = "cancelled"
                save_store(store)
                waiting = [w for w in store["waitlist"] if w.resource_id == item.resource_id and w.booking_date == item.booking_date
                           and overlaps(item.start_time, item.end_time, w.start_time, w.end_time)]
                first = min(waiting, key=lambda w: w.created_at) if waiting else None
                message = f"Booking {item.booking_id} cancelled."
                if first:
                    message += f" Wait-list: {first.user_id} is first for an overlapping slot ({first.start_time}–{first.end_time}); staff confirmation is required."
                self.respond({"message": message, "state": snapshot(item.booking_date)})
                return
            if self.path == "/api/report":
                report = usage_report(store["resources"], store["bookings"])
                saved = save_usage_report(report, DATA_DIR)
                self.respond({"report": report, "saved_to": str(saved.relative_to(ROOT))})
                return
            raise ValueError("Unknown action.")
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            self.respond({"error": str(exc)}, 400)
        except OSError as exc:
            self.respond({"error": f"Could not save the change: {exc}"}, 500)


if __name__ == "__main__":
    port = 8000
    print(f"Library Resource Hub running at http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
