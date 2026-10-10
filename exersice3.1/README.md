# Exercise 3.1 — Equipment Maintenance and Service Database

Python 3 and the standard-library `sqlite3` module are sufficient. From this folder run:

```powershell
python main.py
```

## Web dashboard

Install the optional Flask interface with `python -m pip install -r requirements.txt`,
then run `python webapp.py` and open <http://127.0.0.1:5301>. The dashboard uses
the same SQLite database and supports creating equipment and requests, filtering
requests by status, and recording technician status updates with audit notes. Set
`MAINTENANCE_DB_PATH` to use a separate SQLite file for a fresh demo workspace.

The demonstration creates `maintenance.db` beside the scripts, initializes the schema, seeds 10 synthetic equipment items, 4 technicians, and 15 service requests on the first run, then exercises CRUD, rollback, validation, and reports. It is safe to rerun: seed data is inserted only when the equipment table is empty. Delete `maintenance.db` to start with a fresh sample database.

## Schema and relationships

```text
equipment (1) ───────< service_requests >────── (0..1) technicians
                              (1)
                               |
                               v
                       service_updates (many)
```

- `equipment`: `id` primary key; non-empty `name`, `category`, and `location`; constrained equipment `status`.
- `technicians`: `id` primary key; non-empty `name`, `contact`, and `specialty`.
- `service_requests`: `id` primary key; required equipment foreign key; nullable technician foreign key for unassigned requests; issue, constrained status, UTC ISO timestamp creation and nullable resolution timestamp. Closed requests require a resolution timestamp; active requests must not have one.
- `service_updates`: `id` primary key; request foreign key; non-empty audit notes; UTC update timestamp; non-negative maintenance cost (default 0).

Equipment deletion is restricted while requests reference it. Technician deletion sets existing assignments to null. Deleting a request cascades to its update history. Foreign key enforcement is enabled on the connection.

## Reports

`DatabaseManager` provides overdue requests (default older than seven days), counts by status, average closed-request resolution time in hours, equipment with more than one fault request, monthly update costs grouped by equipment category, equipment without an active request, and requests without service updates. Maintenance cost is recorded on a service update, so the monthly report aggregates those recorded costs; the seed data includes example costs.

## Design notes

`database.py` holds schema creation, connection lifecycle, input validation, CRUD methods, transaction management, report queries, and idempotent sample seeding. `main.py` is the runnable demonstration. Database writes use `?` placeholders for data values; SQL structure is fixed in source. Python checks required text and recognized statuses, while SQLite `NOT NULL`, `CHECK`, primary-key, and foreign-key constraints provide a second enforcement layer. `DatabaseManager` supports `with` so connections close even when a demonstration step fails.
