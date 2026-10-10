# Exercise 1.2: Library Seat and Equipment Booking Simulator

A Flask-based library booking simulator with a responsive dark dashboard and an interactive CLI. Both interfaces use the same booking models and `data/bookings.json` persistent store, export active daily schedules to CSV, and save analytics reports under date-based folders.

## Run

Requires Python 3.10 or newer. From this folder, install dependencies and start Flask:

```console
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5102>. The Flask interface uses Jinja2 templates in `templates/` and browser assets in `static/`. The dashboard supports the resource catalogue, live slot conflict checks, booking and cancellation, booking lookup, daily schedule filtering and CSV export, and usage and cancellation analytics. When a requested slot conflicts, the dashboard offers the automatic wait-list; cancellation surfaces the first matching wait-list user for staff follow-up without automatically creating a booking.

The original interactive terminal menu remains available:

```console
python main.py
```

The first launch creates a starter catalogue if the store has no resources. Edit `data/bookings.json` to add or change resources. Resource IDs must be unique. The `available` field means the resource is enabled for booking; occupied time slots are determined from active bookings.

## Menu

1. View catalogue.
2. Book a resource using a date in `YYYY-MM-DD` format and 24-hour times in `HH:MM` format.
3. Cancel by booking ID. Cancellation retains the record for reporting. If a matching wait-list request exists, the CLI identifies the first person to contact; staff confirmation is needed to create a booking.
4. Search booking history by user or resource ID.
5. View/export a date's active schedule to `data/daily_schedule_<YYYY-MM-DD>.csv`.
6. Print a resource use and cancellation report and save it to `data/reports/<YYYY-MM-DD>/usage_report.txt`.
7. Exit.

Bookings use half-open intervals: `[start, end)`. Thus 09:00–10:00 and 10:00–11:00 are both permitted, while any positive overlap is rejected. Bookings cannot cross midnight or be made for past dates. A conflicting request is automatically placed on the persistent wait-list. Cancellation identifies the first matching request, but it does not silently auto-book or notify an external system.

## Data recovery

On a missing or empty JSON file, the app starts with an empty store and saves a starter catalogue. Malformed JSON or invalid records produce a warning, preserve a copy as `bookings.json.corrupt` when possible, and initialize a clean store. Writes use a temporary file followed by replacement to reduce the chance of partial JSON writes. Keep backups when editing the data manually.

## Files

- `main.py`: menu and booking workflows.
- `app.py`: Flask server and JSON API for the dashboard.
- `templates/`: shared Jinja2 layout, overview, and daily schedule pages.
- `static/css/styles.css`: responsive dark glass UI styles.
- `static/js/main.js`: live dashboard, booking, lookup, schedule, and wait-list interactions.
- `webapp.py` and `web/`: retained legacy standard-library dashboard.
- `models.py`: data structures, strict parsing, and overlap logic.
- `storage.py`: validation, recovery, and JSON persistence.
- `utils.py`: CSV schedule and analytics reporting.
- `data/bookings.json`: sample catalogue and booking history.
- `data/daily_schedule_2026-10-12.csv`: sample schedule export.
- `data/reports/2026-10-09/usage_report.txt`: sample analytics report.
- `TEST_LOG.md`: edge-case verification expectations and execution status.

