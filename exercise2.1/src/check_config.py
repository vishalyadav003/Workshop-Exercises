"""Safe startup configuration check."""

import logging
import sys

from .config import load_settings, validate_settings


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    errors = validate_settings(load_settings())
    if errors:
        for error in errors:
            logging.error("Configuration error: %s", error)
        logging.error("Configuration check failed; values were not displayed.")
        return 1
    logging.info("Configuration check passed; values were not displayed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
