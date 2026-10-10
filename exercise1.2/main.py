"""Menu-driven library seat and equipment booking simulator."""
from datetime import date
from pathlib import Path
import uuid
from models import Resource, Booking, WaitlistEntry, validate_booking, overlaps
from storage import DATA_DIR, DATA_FILE, load_store, save_store
from utils import export_daily_schedule, usage_report, save_usage_report

def seed_resources(store: dict) -> None:
    """Create a small demo catalogue on first launch; users can edit JSON to customize it."""
    if store["resources"]: return
    store["resources"] = [
        Resource("S-101", "Study Seat", "Quiet Zone, Floor 1"),
        Resource("S-102", "Study Seat", "Quiet Zone, Floor 1"),
        Resource("P-201", "Projector", "Equipment Desk"),
        Resource("L-301", "Laptop", "Equipment Desk"),
        Resource("R-401", "Conference Room", "Collaboration Wing, Floor 2"),
    ]

def print_resources(resources: list[Resource]) -> None:
    print("\nRESOURCE CATALOGUE")
    if not resources:
        print("  No resources. Add resources to data/bookings.json.")
        return
    print(f"{'ID':<12} {'TYPE':<14} {'LOCATION':<30} {'STATUS'}")
    for r in resources:
        print(f"{r.resource_id:<12} {r.resource_type:<14} {r.location:<30} {'Available' if r.available else 'Inactive'}")

def book(store: dict) -> None:
    rid = input("Resource ID: ").strip()
    user = input("User ID: ").strip()
    if not user: print("User ID cannot be empty."); return
    resource = next((r for r in store["resources"] if r.resource_id.lower() == rid.lower()), None)
    if resource is None: print("Unknown resource ID."); return
    if not resource.available: print("This resource is inactive."); return
    day, start, end = input("Date (YYYY-MM-DD): ").strip(), input("Start time (HH:MM): ").strip(), input("End time (HH:MM): ").strip()
    try: d, s, e = validate_booking(day, start, end)
    except ValueError as exc: print(f"Invalid booking: {exc}"); return
    collision = any(b.status == "active" and b.resource_id == resource.resource_id and b.booking_date == d.isoformat()
                    and overlaps(start, end, b.start_time, b.end_time) for b in store["bookings"])
    if collision:
        store["waitlist"].append(WaitlistEntry(uuid.uuid4().hex[:12], resource.resource_id, user, d.isoformat(), s.strftime("%H:%M"), e.strftime("%H:%M"), __import__("datetime").datetime.now().isoformat(timespec="seconds")))
        save_store(store)
        print("That slot overlaps an existing booking; your request was added to the wait-list.")
        return
    item = Booking.create(resource.resource_id, user, d, s, e)
    store["bookings"].append(item); save_store(store)
    print(f"Booking confirmed: {item.booking_id}")

def cancel(store: dict) -> None:
    key = input("Booking ID to cancel: ").strip()
    item = next((b for b in store["bookings"] if b.booking_id.lower() == key.lower() and b.status == "active"), None)
    if item is None: print("Active booking not found."); return
    item.status = "cancelled"
    save_store(store)
    print(f"Cancelled booking {item.booking_id}.")
    matching = [w for w in store["waitlist"] if w.resource_id == item.resource_id and w.booking_date == item.booking_date
                and overlaps(item.start_time, item.end_time, w.start_time, w.end_time)]
    if matching:
        first = min(matching, key=lambda w: w.created_at)
        print(f"Wait-list notice: {first.user_id} is first for an overlapping slot ({first.start_time}-{first.end_time}). Contact them to confirm; no automatic booking was made.")

def lookup(store: dict) -> None:
    kind = input("Search by (U)ser ID or (R)esource ID? ").strip().lower()
    value = input("ID: ").strip().lower()
    if kind not in ("u", "r"): print("Choose U or R."); return
    matches = [b for b in store["bookings"] if (b.user_id if kind == "u" else b.resource_id).lower() == value]
    if not matches: print("No bookings found."); return
    for b in sorted(matches, key=lambda x: (x.booking_date, x.start_time)):
        print(f"{b.booking_id} | {b.status.upper():<9} | {b.resource_id} | user {b.user_id} | {b.booking_date} {b.start_time}-{b.end_time}")

def schedule(store: dict) -> None:
    day = input("Schedule date (YYYY-MM-DD): ").strip()
    from models import parse_day
    try: day = parse_day(day).isoformat()
    except ValueError as exc: print(exc); return
    rows = sorted((b for b in store["bookings"] if b.booking_date == day and b.status == "active"), key=lambda x: (x.start_time, x.resource_id))
    print(f"\nSchedule for {day}")
    if rows:
        for b in rows: print(f"{b.start_time}-{b.end_time} | {b.resource_id} | user {b.user_id} | {b.booking_id}")
    else: print("No active bookings.")
    answer = input("Export CSV? (y/N): ").strip().lower()
    if answer == "y": print(f"Exported: {export_daily_schedule(store['bookings'], day, DATA_DIR)}")

def main() -> None:
    store, warning = load_store()
    if warning: print(f"Notice: {warning}")
    seed_resources(store)
    save_store(store)
    while True:
        print("\n=== LIBRARY BOOKING SIMULATOR ===\n1. View Resource Catalogue\n2. Book a Resource\n3. Cancel a Booking\n4. Lookup Bookings\n5. View / Export Daily Schedule\n6. Usage & Cancellation Analytics\n7. Exit")
        choice = input("Select 1-7: ").strip()
        try:
            if choice == "1": print_resources(store["resources"])
            elif choice == "2": book(store)
            elif choice == "3": cancel(store)
            elif choice == "4": lookup(store)
            elif choice == "5": schedule(store)
            elif choice == "6":
                report = usage_report(store["resources"], store["bookings"])
                print("\n" + report)
                print(f"Saved report: {save_usage_report(report, DATA_DIR)}")
            elif choice == "7": print("Goodbye."); break
            else: print("Enter a number from 1 to 7.")
        except (OSError, ValueError) as exc:
            print(f"Operation failed safely: {exc}")

if __name__ == "__main__": main()
