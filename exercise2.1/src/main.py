"""Minimal application entry point demonstrating fail-closed configuration."""

import logging
import sys

from .config import load_settings, validate_settings


def main() -> int:
    settings = load_settings()
    errors = validate_settings(settings)
    if errors:
        for error in errors:
            logging.error("Configuration error: %s", error)
        return 1
    logging.info("Application %s is ready in %s mode.", settings.app_name, settings.app_env)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sys.exit(main())
