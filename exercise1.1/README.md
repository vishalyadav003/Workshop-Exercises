# Campus Event Registration Workflow Simulator

A light-theme Flask web application for creating campus events, registering attendees, tracking seat utilization, cancelling registrations, reviewing activity logs, and exporting an attendance CSV. Events and registrations are stored separately in `data/events.json` and `data/registrations.json`; activity and validation failures are written to `logs/app.log`. The app creates missing JSON arrays on first use and can migrate the earlier combined sample file.

## Run the application

1. Install Python 3.9 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (recommended):

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS/Linux, use `python3 -m venv .venv` and `source .venv/bin/activate`.

4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Start the web server:

   ```bash
   python app.py
   ```

6. Visit [http://127.0.0.1:5101](http://127.0.0.1:5101) in your browser. Stop the server with `Ctrl+C`.

## Run from VS Code

Open this project folder in VS Code, install/select the Python extension and interpreter, then press **F5** and choose **Run CampusFlow** if prompted. VS Code starts the Flask server and opens the website in your browser at `http://127.0.0.1:5051/`.

`templates/index.html` is a Flask/Jinja template, so opening that source file directly will not render the website. Start the Flask app with F5 (or `python app.py`) and visit the local URL instead. To stop the VS Code run, press **Shift+F5**.

## Features

- Four dashboard KPIs, including overall seat utilization.
- Event creation modal and a responsive catalogue with capacity indicators.
- Registration form with live seat availability and ID, duplicate, email, and capacity validation.
- Searchable registration roster with event filtering and confirmation-based AJAX cancellation.
- Attendance CSV download and a timestamped activity-log drawer.
- Persistent JSON data and application audit/error logging.

## Project files

- `app.py`, `models.py`, `utils.py`: Flask routes, domain models, validation, persistence, and logging.
- `templates/base.html`, `templates/index.html`, `templates/events.html`: shared shell and Jinja pages.
- `static/css/styles.css`, `static/js/main.js`: light-theme interface and asynchronous interactions.
- `data/events.json`, `data/registrations.json`: sample event and attendee records.

