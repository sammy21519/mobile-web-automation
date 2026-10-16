"""
Logging helper: console + one log file per run.

Each run writes to its own file named after the time the run started.
"""
import logging
from datetime import datetime

from config import settings

ROOT_LOGGER = "automation"
_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_configured = False


def _setup() -> None:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = settings.LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

    root = logging.getLogger(ROOT_LOGGER)
    root.setLevel(logging.INFO)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(file_handler)
    root.addHandler(console)
    root.info("Logging to %s", log_file)


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        _setup()
        _configured = True
    return logging.getLogger(f"{ROOT_LOGGER}.{name}")
