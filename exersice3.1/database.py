"""SQLite database layer for the equipment maintenance exercise.

All values supplied by callers are bound with sqlite3 placeholders. Identifiers
in this module are fixed in source; user input is never used as SQL syntax.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

DB_PATH = Path(__file__).with_name("maintenance.db")
REQUEST_STATUSES = ("Open", "In Progress", "Closed")
EQUIPMENT_STATUSES = ("Operational", "Under Maintenance", "Out of Service")


class DatabaseManager:
    """Connection owner and CRUD/report API for the maintenance database."""

    def __init__(self, db_path: str | Path = DB_PATH) -> None:
        self.db_path = str(db_path)
        self.connection = sqlite3.connect(self.db_path, timeout=10.0)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 10000")

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "DatabaseManager":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def create_schema(self) -> None:
        """Create tables and indexes; safe to call repeatedly."""
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL CHECK(length(trim(name)) > 0),
            category TEXT NOT NULL CHECK(length(trim(category)) > 0),
            location TEXT NOT NULL CHECK(length(trim(location)) > 0),
            status TEXT NOT NULL DEFAULT 'Operational'
                CHECK(status IN ('Operational','Under Maintenance','Out of Service'))
        );
        CREATE TABLE IF NOT EXISTS technicians (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL CHECK(length(trim(name)) > 0),
            contact TEXT NOT NULL CHECK(length(trim(contact)) > 0),
            specialty TEXT NOT NULL CHECK(length(trim(specialty)) > 0)
        );
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY,
            equipment_id INTEGER NOT NULL REFERENCES equipment(id) ON UPDATE CASCADE ON DELETE RESTRICT,
            technician_id INTEGER REFERENCES technicians(id) ON UPDATE CASCADE ON DELETE SET NULL,
            issue_description TEXT NOT NULL CHECK(length(trim(issue_description)) > 0),
            status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','In Progress','Closed')),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            resolved_at TEXT,
            CHECK((status = 'Closed' AND resolved_at IS NOT NULL) OR
                  (status <> 'Closed' AND resolved_at IS NULL))
        );
        CREATE TABLE IF NOT EXISTS service_updates (
            id INTEGER PRIMARY KEY,
            request_id INTEGER NOT NULL REFERENCES service_requests(id) ON UPDATE CASCADE ON DELETE CASCADE,
            update_notes TEXT NOT NULL CHECK(length(trim(update_notes)) > 0),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
            cost REAL NOT NULL DEFAULT 0 CHECK(cost >= 0)
        );
        CREATE INDEX IF NOT EXISTS idx_requests_status_created ON service_requests(status, created_at);
        CREATE INDEX IF NOT EXISTS idx_requests_equipment ON service_requests(equipment_id);
        CREATE INDEX IF NOT EXISTS idx_updates_request ON service_updates(request_id);
        """)
        self.connection.commit()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Run a group of writes atomically, rolling back on any exception."""
        try:
            with self.connection:
                yield self.connection
        except sqlite3.Error:
            raise

    @staticmethod
    def _required(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must not be empty")
        return value.strip()

    def add_equipment(self, name: str, category: str, location: str,
                      status: str = "Operational", equipment_id: int | None = None) -> int:
        name, category, location = (self._required(v, k) for v, k in
                                     ((name, "name"), (category, "category"), (location, "location")))
        if status not in EQUIPMENT_STATUSES:
            raise ValueError(f"status must be one of {EQUIPMENT_STATUSES}")
        if equipment_id is None:
            cur = self.connection.execute(
                "INSERT INTO equipment(name,category,location,status) VALUES(?,?,?,?)",
                (name, category, location, status))
        else:
            cur = self.connection.execute(
                "INSERT INTO equipment(id,name,category,location,status) VALUES(?,?,?,?,?)",
                (equipment_id, name, category, location, status))
        self.connection.commit()
        return int(cur.lastrowid)

    def add_technician(self, name: str, contact: str, specialty: str,
                       technician_id: int | None = None) -> int:
        values = tuple(self._required(v, k) for v, k in
                       ((name, "name"), (contact, "contact"), (specialty, "specialty")))
        if technician_id is None:
            cur = self.connection.execute("INSERT INTO technicians(name,contact,specialty) VALUES(?,?,?)", values)
        else:
            cur = self.connection.execute("INSERT INTO technicians(id,name,contact,specialty) VALUES(?,?,?,?)",
                                          (technician_id, *values))
        self.connection.commit()
        return int(cur.lastrowid)

    def create_request(self, equipment_id: int, issue_description: str,
                       technician_id: int | None = None, request_id: int | None = None,
                       created_at: str | None = None) -> int:
        issue = self._required(issue_description, "issue_description")
        if request_id is None and created_at is None:
            cur = self.connection.execute(
                "INSERT INTO service_requests(equipment_id,technician_id,issue_description) VALUES(?,?,?)",
                (equipment_id, technician_id, issue))
        elif request_id is None:
            cur = self.connection.execute(
                "INSERT INTO service_requests(equipment_id,technician_id,issue_description,created_at) VALUES(?,?,?,?)",
                (equipment_id, technician_id, issue, created_at))
        else:
            cur = self.connection.execute(
                "INSERT INTO service_requests(id,equipment_id,technician_id,issue_description,created_at) VALUES(?,?,?,?,?)",
                (request_id, equipment_id, technician_id, issue, created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        self.connection.commit()
        return int(cur.lastrowid)

    def get_request(self, request_id: int) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM service_requests WHERE id = ?", (request_id,)).fetchone()
        return dict(row) if row else None

    def list_requests(self, status: str | None = None) -> list[dict[str, Any]]:
        if status is None:
            rows = self.connection.execute("SELECT * FROM service_requests ORDER BY id").fetchall()
        else:
            if status not in REQUEST_STATUSES:
                raise ValueError(f"status must be one of {REQUEST_STATUSES}")
            rows = self.connection.execute("SELECT * FROM service_requests WHERE status = ? ORDER BY id", (status,)).fetchall()
        return [dict(row) for row in rows]

    def update_request_status(self, request_id: int, status: str, notes: str) -> None:
        """Atomically update status/timestamp and append its audit entry."""
        notes = self._required(notes, "notes")
        if status not in REQUEST_STATUSES:
            raise ValueError(f"status must be one of {REQUEST_STATUSES}")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        resolved_at = now if status == "Closed" else None
        with self.transaction() as conn:
            cur = conn.execute("UPDATE service_requests SET status = ?, resolved_at = ? WHERE id = ?",
                               (status, resolved_at, request_id))
            if cur.rowcount != 1:
                raise LookupError(f"service request {request_id} not found")
            conn.execute("INSERT INTO service_updates(request_id,update_notes,updated_at) VALUES(?,?,?)",
                         (request_id, notes, now))

    def list_overdue_requests(self, days: int = 7) -> list[dict[str, Any]]:
        if days < 0:
            raise ValueError("days must be non-negative")
        rows = self.connection.execute("""
            SELECT r.*, e.name AS equipment_name
            FROM service_requests r JOIN equipment e ON e.id=r.equipment_id
            WHERE r.status <> 'Closed' AND r.created_at < datetime('now', ?)
            ORDER BY r.created_at
        """, (f"-{days} days",)).fetchall()
        return [dict(row) for row in rows]

    def count_requests_by_status(self) -> dict[str, int]:
        counts = {status: 0 for status in REQUEST_STATUSES}
        for row in self.connection.execute("SELECT status, COUNT(*) AS total FROM service_requests GROUP BY status"):
            counts[row["status"]] = int(row["total"])
        return counts

    def average_resolution_hours(self) -> float | None:
        row = self.connection.execute("""
            SELECT AVG((julianday(resolved_at)-julianday(created_at))*24.0) AS hours
            FROM service_requests WHERE status='Closed' AND resolved_at IS NOT NULL
        """).fetchone()
        return float(row["hours"]) if row and row["hours"] is not None else None

    def repeated_faults(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("""
            SELECT e.id, e.name, e.category, COUNT(r.id) AS fault_count
            FROM equipment e JOIN service_requests r ON r.equipment_id=e.id
            GROUP BY e.id,e.name,e.category HAVING COUNT(r.id)>1 ORDER BY fault_count DESC,e.name
        """).fetchall()
        return [dict(row) for row in rows]

    def monthly_maintenance_costs(self) -> list[dict[str, Any]]:
        """Monthly costs by category; cost is captured per service update."""
        rows = self.connection.execute("""
            SELECT strftime('%Y-%m',u.updated_at) AS month,e.category,
                   ROUND(SUM(u.cost),2) AS total_cost,COUNT(DISTINCT r.id) AS request_count
            FROM service_updates u JOIN service_requests r ON r.id=u.request_id
            JOIN equipment e ON e.id=r.equipment_id
            GROUP BY month,e.category ORDER BY month,e.category
        """).fetchall()
        return [dict(row) for row in rows]

    def add_update(self, request_id: int, notes: str, cost: float = 0.0) -> int:
        notes = self._required(notes, "notes")
        if cost < 0:
            raise ValueError("cost must be non-negative")
        cur = self.connection.execute(
            "INSERT INTO service_updates(request_id,update_notes,cost) VALUES(?,?,?)",
            (request_id, notes, cost))
        self.connection.commit()
        return int(cur.lastrowid)

    def unassigned_equipment(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("""
            SELECT e.* FROM equipment e
            WHERE NOT EXISTS (SELECT 1 FROM service_requests r WHERE r.equipment_id=e.id AND r.status<>'Closed')
            ORDER BY e.id
        """).fetchall()
        return [dict(row) for row in rows]

    def unassigned_requests(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT * FROM service_requests WHERE technician_id IS NULL ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

    def requests_without_updates(self) -> list[dict[str, Any]]:
        rows = self.connection.execute("""
            SELECT r.* FROM service_requests r
            WHERE NOT EXISTS (SELECT 1 FROM service_updates u WHERE u.request_id=r.id) ORDER BY r.id
        """).fetchall()
        return [dict(row) for row in rows]


def seed_database(db: DatabaseManager) -> None:
    """Insert the deterministic synthetic dataset once into an empty database."""
    if db.connection.execute("SELECT 1 FROM equipment LIMIT 1").fetchone():
        return
    equipment = [
        (1,"Centrifuge A","Analytical","Lab 1"),(2,"Microscope B","Optical","Lab 1"),
        (3,"Autoclave C","Sterilization","Room 2"),(4,"Freezer D","Cold Storage","Room 2"),
        (5,"Spectrometer E","Analytical","Lab 3"),(6,"Pump F","Fluid Handling","Lab 3"),
        (7,"Incubator G","Environmental","Room 4"),(8,"Balance H","Analytical","Lab 4"),
        (9,"PCR System I","Molecular","Lab 5"),(10,"Water Purifier J","Fluid Handling","Room 1"),
    ]
    technicians = [(1,"Asha Rao","555-0101","Electrical"),(2,"Ben Carter","555-0102","Optical"),
                   (3,"Chen Li","555-0103","Mechanical"),(4,"Dina Patel","555-0104","Calibration")]
    requests = [
        (1,1,"Rotor vibration above normal",1,"In Progress",-20),(2,2,"Lamp flickers",2,"Closed",-18),
        (3,3,"Door seal leak",3,"Open",-16),(4,4,"Temperature alarm",3,"In Progress",-15),
        (5,5,"Wavelength reading drift",4,"Closed",-14),(6,6,"Pressure fluctuation",3,"Open",-12),
        (7,7,"Temperature control failure",1,"Closed",-11),(8,8,"Calibration overdue",4,"Open",-10),
        (9,9,"Amplification error",1,"In Progress",-9),(10,10,"Filter warning",3,"Open",-8),
        (11,1,"Motor noise returned",3,"Open",-7),(12,2,"Stage movement sticks",2,"Closed",-6),
        (13,4,"Compressor cycles frequently",3,"Open",-5),(14,5,"Display intermittently blank",2,"In Progress",-3),
        (15,1,"Rotor imbalance",1,"Closed",-2),
    ]
    with db.transaction() as conn:
        conn.executemany("INSERT INTO equipment(id,name,category,location) VALUES(?,?,?,?)", equipment)
        conn.executemany("INSERT INTO technicians(id,name,contact,specialty) VALUES(?,?,?,?)", technicians)
        for rid,eid,issue,tid,status,age in requests:
            created = conn.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ','now',?)", (f"{age} days",)).fetchone()[0]
            resolved = conn.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ','now',?)", (f"{age+1} days",)).fetchone()[0] if status == "Closed" else None
            conn.execute("""INSERT INTO service_requests(id,equipment_id,technician_id,issue_description,status,created_at,resolved_at)
                            VALUES(?,?,?,?,?,?,?)""", (rid,eid,tid,issue,status,created,resolved))
        conn.executemany("INSERT INTO service_updates(request_id,update_notes,cost) VALUES(?,?,?)", [
            (1,"Initial diagnostic inspection",45.00),
            (2,"Lamp replaced and verified",28.50),
            (5,"Optics recalibrated",72.00),
            (7,"Controller replaced",110.00),
        ])
