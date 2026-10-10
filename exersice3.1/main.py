"""Run the Exercise 3.1 database demonstration: python main.py"""
from __future__ import annotations

import json
import sqlite3

from database import DatabaseManager, seed_database


def show(title: str, value: object) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(value, indent=2, default=str))


def demonstrate_rollback(db: DatabaseManager) -> None:
    """Simulate failure after both writes and verify neither is committed."""
    request_id = 1
    before = db.get_request(request_id)
    updates_before = db.connection.execute(
        "SELECT COUNT(*) FROM service_updates WHERE request_id = ?", (request_id,)
    ).fetchone()[0]
    try:
        with db.transaction() as conn:
            conn.execute("UPDATE service_requests SET status=?,resolved_at=? WHERE id=?",
                         ("Closed", "2026-01-01T00:00:00Z", request_id))
            conn.execute("INSERT INTO service_updates(request_id,update_notes) VALUES(?,?)",
                         (request_id, "Simulated update that must roll back"))
            raise sqlite3.OperationalError("simulated database failure")
    except sqlite3.Error as exc:
        print(f"Rollback demonstrated: {exc}")
    after = db.get_request(request_id)
    updates_after = db.connection.execute(
        "SELECT COUNT(*) FROM service_updates WHERE request_id = ?", (request_id,)
    ).fetchone()[0]
    assert after == before and updates_after == updates_before, "Rollback verification failed"
    print("Verified: status and update count are unchanged after rollback.")


def demonstrate_validation(db: DatabaseManager) -> None:
    """Show duplicate-key, invalid-status, empty-field and injection resilience."""
    checks = [
        ("duplicate primary key", lambda: db.add_equipment("Duplicate", "Test", "Lab", equipment_id=1)),
        ("invalid status", lambda: db.update_request_status(1, "Definitely not a status", "test")),
        ("empty field", lambda: db.add_equipment("  ", "Test", "Lab")),
        ("injection payload", lambda: db.list_requests("' OR '1'='1")),
    ]
    for name, operation in checks:
        try:
            operation()
        except (sqlite3.Error, ValueError) as exc:
            print(f"Rejected {name}: {type(exc).__name__}: {exc}")
        else:
            raise AssertionError(f"Expected {name} to be rejected")
    # The malicious-looking description is ordinary data when parameterized.
    payload = "Pump alert ' OR '1'='1"
    new_id = db.create_request(10, payload)
    assert db.get_request(new_id)["issue_description"] == payload
    print("Injection-shaped description was stored as literal data; it did not alter query logic.")


def main() -> None:
    with DatabaseManager() as db:
        db.create_schema()
        seed_database(db)

        # CRUD demonstration: Create, Read, Update (with audit trail), and Close.
        equipment_id = db.add_equipment("Demo analyzer", "Analytical", "Training Lab")
        request_id = db.create_request(equipment_id, "Demonstration self-check", technician_id=1)
        show("Created request", db.get_request(request_id))
        db.update_request_status(request_id, "In Progress", "Technician began inspection")
        show("Requests in progress", db.list_requests("In Progress"))
        db.update_request_status(request_id, "Closed", "Self-check passed; closed")
        show("Closed request", db.get_request(request_id))

        demonstrate_rollback(db)
        demonstrate_validation(db)
        show("Overdue requests (older than 7 days)", db.list_overdue_requests(7))
        show("Request counts by status", db.count_requests_by_status())
        show("Average resolution time in hours", db.average_resolution_hours())
        show("Equipment with repeated faults", db.repeated_faults())
        show("Monthly maintenance costs by category", db.monthly_maintenance_costs())
        show("Unassigned equipment (no active request)", db.unassigned_equipment())
        show("Requests without an assigned technician", db.unassigned_requests())
        show("Requests without service updates", db.requests_without_updates())
        print("\nDatabase connection closed by context manager.")


if __name__ == "__main__":
    main()
