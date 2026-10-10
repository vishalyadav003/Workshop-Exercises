"""Data models and validation for the booking simulator."""
from dataclasses import dataclass, asdict
from datetime import date, time, datetime
from typing import Any
import uuid

@dataclass
class Resource:
    resource_id: str
    resource_type: str
    location: str
    available: bool = True

@dataclass
class Booking:
    booking_id: str
    resource_id: str
    user_id: str
    booking_date: str
    start_time: str
    end_time: str
    status: str = "active"
    created_at: str = ""

    @classmethod
    def create(cls, resource_id: str, user_id: str, day: date, start: time, end: time):
        return cls(uuid.uuid4().hex[:12], resource_id, user_id, day.isoformat(),
                   start.strftime("%H:%M"), end.strftime("%H:%M"), "active", datetime.now().isoformat(timespec="seconds"))

@dataclass
class WaitlistEntry:
    waitlist_id: str
    resource_id: str
    user_id: str
    booking_date: str
    start_time: str
    end_time: str
    created_at: str

def parse_day(value: str) -> date:
    """Accept only the unambiguous ISO date format YYYY-MM-DD."""
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError) as exc:
        raise ValueError("Date must use YYYY-MM-DD and be a real calendar date.") from exc
    if parsed.isoformat() != value.strip():
        raise ValueError("Date must use YYYY-MM-DD.")
    return parsed

def parse_clock(value: str) -> time:
    """Accept 24-hour HH:MM times only."""
    try:
        parsed = datetime.strptime(value.strip(), "%H:%M").time()
    except (ValueError, AttributeError) as exc:
        raise ValueError("Time must use 24-hour HH:MM format (for example 09:30).") from exc
    if parsed.strftime("%H:%M") != value.strip():
        raise ValueError("Time must use zero-padded HH:MM format.")
    return parsed

def overlaps(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    """Half-open intervals: an end exactly at the next start is allowed."""
    a0, a1 = parse_clock(start_a), parse_clock(end_a)
    b0, b1 = parse_clock(start_b), parse_clock(end_b)
    return a0 < b1 and b0 < a1

def validate_booking(day: str, start: str, end: str) -> tuple[date, time, time]:
    d, s, e = parse_day(day), parse_clock(start), parse_clock(end)
    if e <= s:
        raise ValueError("End time must be later than start time; bookings cannot cross midnight.")
    if d < date.today():
        raise ValueError("Bookings cannot be made for a past date.")
    return d, s, e

def resource_from_dict(item: dict[str, Any]) -> Resource:
    return Resource(str(item["resource_id"]), str(item["resource_type"]), str(item["location"]), bool(item.get("available", True)))

def booking_from_dict(item: dict[str, Any]) -> Booking:
    booking = Booking(**{k: item[k] for k in ("booking_id", "resource_id", "user_id", "booking_date", "start_time", "end_time")},
                      status=item.get("status", "active"), created_at=item.get("created_at", ""))
    # Historical bookings remain valid records even though new bookings cannot be backdated.
    parse_day(booking.booking_date)
    if parse_clock(booking.end_time) <= parse_clock(booking.start_time):
        raise ValueError("Invalid stored time interval")
    if booking.status not in ("active", "cancelled"):
        raise ValueError("Unknown booking status")
    return booking
