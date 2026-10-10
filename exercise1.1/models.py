"""Domain models for the campus event registration simulator."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class Event:
    event_id: str
    name: str
    capacity: int

    def to_dict(self):
        return asdict(self)


@dataclass
class Registration:
    participant_id: str
    name: str
    email: str
    event_id: str
    registered_at: str

    @classmethod
    def create(cls, participant_id, name, email, event_id):
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return cls(participant_id, name, email, event_id, timestamp)

    def to_dict(self):
        return asdict(self)
