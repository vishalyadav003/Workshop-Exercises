"""Schedule export and analytics helpers."""
import csv
from collections import Counter
from datetime import date
from pathlib import Path
from models import Booking

def export_daily_schedule(bookings: list[Booking], day: str, data_dir: Path) -> Path:
    destination = data_dir / f"daily_schedule_{day}.csv"
    rows = sorted((b for b in bookings if b.booking_date == day and b.status == "active"),
                  key=lambda b: (b.start_time, b.resource_id))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["booking_id", "resource_id", "user_id", "date", "start_time", "end_time", "status"])
        for b in rows:
            writer.writerow([b.booking_id, b.resource_id, b.user_id, b.booking_date, b.start_time, b.end_time, b.status])
    return destination

def usage_report(resources: list, bookings: list[Booking]) -> str:
    counts = Counter(b.resource_id for b in bookings if b.status == "active")
    names = {r.resource_id: f"{r.resource_id} ({r.resource_type}, {r.location})" for r in resources}
    ranking = sorted(resources, key=lambda r: (-counts[r.resource_id], r.resource_id))
    lines = ["RESOURCE USAGE & CANCELLATION REPORT", "Active booking count per resource:"]
    if not resources: lines.append("  No resources registered.")
    for r in ranking: lines.append(f"  {names[r.resource_id]}: {counts[r.resource_id]}")
    cancelled = [b for b in bookings if b.status == "cancelled"]
    lines += [f"\nCancelled bookings ({len(cancelled)}):"]
    if not cancelled: lines.append("  None.")
    for b in sorted(cancelled, key=lambda x: (x.booking_date, x.start_time)):
        lines.append(f"  {b.booking_id} | {b.resource_id} | user {b.user_id} | {b.booking_date} {b.start_time}-{b.end_time}")
    return "\n".join(lines)

def save_usage_report(text: str, data_dir: Path, day: date | None = None) -> Path:
    """Place the report in a date-based folder, e.g. data/reports/2026-10-09."""
    folder = data_dir / "reports" / (day or date.today()).isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "usage_report.txt"
    target.write_text(text + "\n", encoding="utf-8")
    return target
