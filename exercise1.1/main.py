"""Campus Event Registration Workflow Simulator. Run with: python main.py"""
import csv
import logging
from pathlib import Path

from models import Event, Registration
from utils import (CSV_FILE, DATA_FILE, get_logger, load_data, save_data,
                   validate_email, validate_identifier, validate_text)

LOGGER = get_logger()

class RegistrationService:
    """Application logic; all writes are persisted before reporting success."""
    def __init__(self, data_file=DATA_FILE):
        self.data_file = Path(data_file)

    def add_event(self, event_id, name, capacity):
        try:
            event_id = validate_identifier(event_id, "Event ID")
            name = validate_text(name, "Event name")
            capacity = int(capacity)
            if capacity <= 0:
                raise ValueError("Capacity must be a positive whole number")
            data = load_data(self.data_file)
            if any(e.get("event_id", "").casefold() == event_id.casefold() for e in data["events"]):
                raise ValueError("Event ID already exists")
            data["events"].append(Event(event_id, name, capacity).to_dict())
            save_data(data, self.data_file)
            return True
        except (ValueError, OSError) as exc:
            LOGGER.warning("EVENT_ADD_FAILED event_id=%r reason=%s", event_id, exc)
            raise

    def register(self, participant_id, name, email, event_id):
        try:
            participant_id = validate_identifier(participant_id, "Participant ID")
            name = validate_text(name, "Participant name")
            email = validate_email(email)
            event_id = validate_identifier(event_id, "Event ID")
            data = load_data(self.data_file)
            event = next((e for e in data["events"] if e.get("event_id", "").casefold() == event_id.casefold()), None)
            if event is None:
                raise ValueError("Event not found")
            count = sum(1 for r in data["registrations"] if r.get("event_id", "").casefold() == event_id.casefold())
            if count >= event["capacity"]:
                raise ValueError("Event is full; no seats are available")
            if any(r.get("participant_id", "").casefold() == participant_id.casefold() and r.get("event_id", "").casefold() == event_id.casefold() for r in data["registrations"]):
                raise ValueError("Participant is already registered for this event")
            data["registrations"].append(Registration.create(participant_id, name, email, event["event_id"]).to_dict())
            save_data(data, self.data_file)
            LOGGER.info("REGISTRATION_SUCCESS participant_id=%s event_id=%s", participant_id, event_id)
            return True
        except (ValueError, OSError) as exc:
            LOGGER.warning("REGISTRATION_FAILED participant_id=%r event_id=%r reason=%s", participant_id, event_id, exc)
            raise

    def cancel(self, participant_id, event_id):
        try:
            participant_id = validate_identifier(participant_id, "Participant ID")
            event_id = validate_identifier(event_id, "Event ID")
            data = load_data(self.data_file)
            kept = [r for r in data["registrations"] if not (r.get("participant_id", "").casefold() == participant_id.casefold() and r.get("event_id", "").casefold() == event_id.casefold())]
            if len(kept) == len(data["registrations"]):
                raise ValueError("Registration not found")
            data["registrations"] = kept
            save_data(data, self.data_file)
            LOGGER.info("CANCELLATION_SUCCESS participant_id=%s event_id=%s", participant_id, event_id)
            return True
        except (ValueError, OSError) as exc:
            LOGGER.warning("CANCELLATION_FAILED participant_id=%r event_id=%r reason=%s", participant_id, event_id, exc)
            raise

    def registrations(self):
        data = load_data(self.data_file)
        names = {e["event_id"]: e["name"] for e in data["events"]}
        return [(r, names.get(r.get("event_id"), "[unknown event]")) for r in data["registrations"]]

    def summary(self):
        data = load_data(self.data_file)
        rows = []
        for event in data["events"]:
            count = sum(r.get("event_id", "").casefold() == event["event_id"].casefold() for r in data["registrations"])
            rows.append((event["event_id"], event["name"], count, event["capacity"] - count))
        return rows

    def export_csv(self, csv_file=CSV_FILE):
        rows = self.registrations()
        path = Path(csv_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Use a temporary file to avoid leaving a truncated attendance sheet.
        import os, tempfile
        fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Participant ID", "Name", "Email", "Event ID", "Event Name", "Registered At (UTC)"])
                for r, event_name in rows:
                    writer.writerow([r.get("participant_id", ""), r.get("name", ""), r.get("email", ""), r.get("event_id", ""), event_name, r.get("registered_at", "")])
            os.replace(tmp, path)
        except Exception:
            try: os.unlink(tmp)
            except OSError: pass
            raise
        return len(rows)

def prompt(label):
    try:
        return input(label).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nInput ended. Returning to menu.")
        return ""

def run():
    service = RegistrationService()
    actions = {
        "1": ("Add technical event", lambda: service.add_event(prompt("Event ID: "), prompt("Event name: "), prompt("Total capacity: "))),
        "2": ("Register participant", lambda: service.register(prompt("Participant ID: "), prompt("Name: "), prompt("Email: "), prompt("Event ID: "))),
        "3": ("Cancel registration", lambda: service.cancel(prompt("Participant ID: "), prompt("Event ID: "))),
    }
    while True:
        print("\n=== Campus Event Registration ===\n1. Add technical event\n2. Register participant\n3. Cancel registration\n4. List all registrations\n5. Export attendance sheet to CSV\n6. Generate summary report\n7. Exit")
        choice = prompt("Select 1-7: ")
        try:
            if choice == "7":
                print("Goodbye.")
                return
            if choice in actions:
                actions[choice][1]()
                print("Success.")
            elif choice == "4":
                rows = service.registrations()
                if not rows: print("No registrations found.")
                for r, event in rows:
                    print(f"{r.get('participant_id')} | {r.get('name')} | {r.get('email')} | {r.get('event_id')} - {event} | {r.get('registered_at')}")
            elif choice == "5":
                count = service.export_csv()
                print(f"Exported {count} registration(s) to {CSV_FILE}")
            elif choice == "6":
                rows = service.summary()
                if not rows: print("No events found.")
                for eid, name, count, available in rows:
                    print(f"{eid} | {name} | registered: {count} | available: {available}")
            else:
                print("Choose a menu option from 1 to 7.")
        except (ValueError, OSError) as exc:
            LOGGER.error("VALIDATION_OR_OPERATION_ERROR choice=%r reason=%s", choice, exc)
            print(f"Error: {exc}")
        except Exception:
            LOGGER.exception("UNEXPECTED_ERROR choice=%r", choice)
            print("Unexpected error. See logs/app.log for details.")

if __name__ == "__main__":
    run()
