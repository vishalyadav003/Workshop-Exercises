"""Optional browser dashboard backed by the existing registration service."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from main import RegistrationService
from utils import BASE_DIR, DATA_FILE, CSV_FILE, load_data

WEB_DIR = BASE_DIR / "web"
SERVICE = RegistrationService()

def dashboard_state():
    data = load_data(DATA_FILE)
    counts = {event["event_id"].casefold(): 0 for event in data["events"]}
    for registration in data["registrations"]:
        key = registration.get("event_id", "").casefold()
        if key in counts: counts[key] += 1
    events = [{**event, "registered": counts.get(event["event_id"].casefold(), 0), "available": max(0, event["capacity"] - counts.get(event["event_id"].casefold(), 0))} for event in data["events"]]
    names = {event["event_id"].casefold(): event["name"] for event in data["events"]}
    registrations = [{**r, "event_name": names.get(r.get("event_id", "").casefold(), "[unknown event]")} for r in data["registrations"]]
    return {"events": events, "registrations": registrations, "summary": {"events": len(events), "registrations": len(registrations), "available_seats": sum(e["available"] for e in events), "capacity": sum(e["capacity"] for e in events)}}

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): print(f"[{self.log_date_time_string()}] {fmt % args}")
    def respond(self, body, status=200, content_type="application/json; charset=utf-8", headers=None):
        payload = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(payload))); self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items(): self.send_header(key, value)
        self.end_headers(); self.wfile.write(payload)
    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/state": self.respond(dashboard_state()); return
            if path == "/api/export":
                SERVICE.export_csv(CSV_FILE)
                self.respond(Path(CSV_FILE).read_bytes(), content_type="text/csv; charset=utf-8", headers={"Content-Disposition": 'attachment; filename="attendance.csv"'}); return
            if path == "/": self.respond((WEB_DIR / "index.html").read_bytes(), content_type="text/html; charset=utf-8"); return
            if path in ("/styles.css", "/app.js"):
                target = WEB_DIR / path.lstrip("/")
                kind = "text/css; charset=utf-8" if target.suffix == ".css" else "text/javascript; charset=utf-8"
                self.respond(target.read_bytes(), content_type=kind); return
            self.respond({"error": "Not found"}, 404)
        except (ValueError, OSError) as exc: self.respond({"error": str(exc)}, 400)
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0")); payload = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/events":
                SERVICE.add_event(payload.get("event_id", ""), payload.get("name", ""), payload.get("capacity", "")); message = "Event created successfully."
            elif self.path == "/api/registrations":
                SERVICE.register(payload.get("participant_id", ""), payload.get("name", ""), payload.get("email", ""), payload.get("event_id", "")); message = "Registration confirmed. You’re on the list."
            elif self.path == "/api/cancel":
                SERVICE.cancel(payload.get("participant_id", ""), payload.get("event_id", "")); message = "Registration cancelled. The seat is available again."
            else: self.respond({"error": "Unknown action."}, 404); return
            self.respond({"message": message, "state": dashboard_state()})
        except (ValueError, OSError, json.JSONDecodeError) as exc: self.respond({"error": str(exc)}, 400)

if __name__ == "__main__":
    port = 8765
    print(f"Campus Event dashboard running at http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), DashboardHandler).serve_forever()
