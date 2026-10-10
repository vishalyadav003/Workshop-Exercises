"""Pre-run audit for interpreter, declared dependencies, and required env keys."""

import importlib.metadata
import logging
import os
from pathlib import Path
import sys

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"
REQUIRED_ENV = ("APP_ENV", "APP_NAME", "API_TOKEN", "LOG_LEVEL")


def _required_distributions(path: Path) -> list[str]:
    packages = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(("-", "git+", "http:" , "https:")):
            continue
        name = line.split("[", 1)[0].split("==", 1)[0].split(">=", 1)[0].split("<=", 1)[0].strip()
        if name:
            packages.append(name)
    return packages


def audit() -> list[str]:
    errors = []
    if sys.version_info < (3, 8):
        errors.append("Python 3.8 or newer is required")
    if not REQUIREMENTS.is_file():
        errors.append("requirements.txt is missing")
    else:
        for package in _required_distributions(REQUIREMENTS):
            try:
                importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                errors.append("Required dependency is not installed: " + package)
    # Load the project's .env without printing any values; existing process env wins.
    dotenv_path = ROOT / ".env"
    file_values = dotenv_values(dotenv_path) if dotenv_path.is_file() else {}
    missing = [key for key in REQUIRED_ENV if not (os.environ.get(key) or file_values.get(key) or "").strip()]
    if missing:
        errors.append("Missing required environment variable(s): " + ", ".join(missing))
    return errors


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    errors = audit()
    if errors:
        for error in errors:
            logging.error("Environment audit: %s", error)
        logging.error("Audit failed; environment values were not displayed.")
        return 1
    logging.info("Environment audit passed; values were not displayed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
