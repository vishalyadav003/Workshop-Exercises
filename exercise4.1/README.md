# Exercise 4.1 — Flask Lost-and-Found Notice Board

A small Flask application for campus members to post lost/found notices, browse active posts, and mark a notice resolved. It uses a JSON file for persistence so it runs without a database server.

## Run it

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5401`. Set `FLASK_SECRET_KEY` to a long random value outside this classroom demo. Set `NOTICE_DATA_FILE` to choose a different JSON data path. Errors are written to `logs/app.log`; the UI shows generic error text. Do not run Flask's debug server with debug enabled in production.

## Project layout

| File | Purpose |
| --- | --- |
| `app.py` | App factory, configuration, logging, generic 404/500 pages |
| `routes.py` | GET/POST routes, filters, form validation, CSRF/replay guard, PRG redirects |
| `models.py` | JSON persistence and notice operations |
| `data/notices.json` | Sample active and resolved notices; new entries are saved here |
| `templates/` | Base, browse, create, detail, and error pages |
| `static/css/style.css` | Responsive visual styling |

## Routes

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/` | Shows active notices; optional `q`, `category`, and `zone` query filters |
| GET | `/notice/<id>` | Shows notice details and resolved status |
| GET, POST | `/create` | Displays and validates the new notice form |
| POST | `/notice/<id>/resolve` | Idempotently marks a notice resolved and redirects |

The create and resolve forms use a session token, and successful submissions return `303 See Other` redirects to prevent browser refresh from repeating a mutation. Input is validated on the server even when browser validation is present. Template autoescaping is enabled by Jinja.

## Route and validation test table

Use the sample data IDs from `data/notices.json`. All mutations should be tested against a disposable copy of the data file (set `NOTICE_DATA_FILE`) to preserve the sample.

| Test | Request/action | Expected result |
| --- | --- | --- |
| Browse active notices | `GET /` | `200`; resolved sample notice is absent |
| Search and filter | `GET /?q=earbuds&category=Electronics&zone=Library` | `200`; matching active notice displayed |
| Detail exists | `GET /notice/n-20261008-001` | `200`; all notice fields displayed |
| Missing detail | `GET /notice/no-such-id` | Friendly 404 page; status `404` |
| Valid create | Open `/create`, submit all fields with the returned CSRF token | One new unique ID and timestamp saved; `303` to detail |
| Empty required value | POST `/create` with a valid token but empty category, description, zone, date, or contact | `400`; field error shown; no record saved |
| Invalid category/kind/zone | POST a value outside the supported choices with a valid token | `400`; validation error; no record saved |
| Too-long description | POST a description of 1001 characters with a valid token | `400`; length error; no record saved |
| Invalid/future date | POST malformed date or a future date with a valid token | `400`; date error; no record saved |
| Duplicate create submission | Repeat the same POST with the already-used form token | `303` back to create; exactly one record was created |
| Resolve via POST | Submit resolve form on an active notice | `303` to detail; JSON has `resolved: true` |
| Resolve replay | Repeat the same POST/token | `303`; remains resolved, no duplicate record or mutation |
| Resolve missing ID | POST `/notice/no-such-id/resolve` with a fresh valid token | Friendly 404 page; status `404` |
| Unknown route | `GET /not-a-route` | Friendly 404 page; status `404` |
| Generic server error | In a controlled local development run, trigger an unexpected exception | Friendly 500 page; details in `logs/app.log` |

## Notes

Contact preference is intentionally a free-text dummy channel such as “Library help desk”; users should not enter personal phone numbers or email addresses. JSON persistence is appropriate for this exercise but is not intended for concurrent production traffic. Replace it with SQLite and migrations for a multi-user deployment.
