# Exercise 2.1: Reproducible Python Project and Dependency Audit

A small, reproducible Python project demonstrating isolated dependencies, environment-based configuration, and a pre-run audit. The starter application validates its configuration and prints only safe status messages.

## Requirements

- Python 3.8 or newer
- pip

## Setup

From this directory, create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy the example using `cp .env.example .env`.

Edit `.env` with local, non-production values. Do not commit `.env`. The supplied example uses placeholders only.

## Run checks

```powershell
python -m src.validate_env
python -m src.check_config
python -m unittest discover -s tests -v
```

## Web dashboard

Install the packages in `requirements.txt`, then run `python webapp.py` and open
<http://127.0.0.1:5201>. The dashboard reports Python, installed dependencies,
and safe configuration readiness without displaying secret values. The CLI
checks above remain available for automation.

`validate_env` checks Python compatibility, installed requirements, and required environment keys. `check_config` validates configuration without echoing values. The app example can be run with `python -m src.main`.

## Reproducibility

`requirements.txt` pins the direct runtime dependency. `pyproject.toml` declares project metadata and the supported Python range. Use the same Python version and install from the pinned requirements in each isolated environment. For a fully transitive lock, generate and commit a platform-appropriate lock file as a team policy.

## Project tree

```text
.
├── data/                 # local or sample data (no secrets)
├── docs/dependency_inventory.md
├── logs/                  # runtime logs (ignored by Git)
├── src/
│   ├── check_config.py
│   ├── config.py
│   ├── main.py
│   └── validate_env.py
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── requirements.txt
```

## Security assurance

The committed `.env.example` contains placeholders, not credentials. Configuration values are never printed by the startup checks or sample app. `.env`, virtual environments, logs, and Python cache files are excluded by `.gitignore`. Review local data and logs before sharing the project; this starter does not claim to inspect secrets in arbitrary files.
