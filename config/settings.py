"""
Framework-wide configuration: browser, device, timeouts and output folders.

Nothing here belongs to a specific website or test case. Test data such as
URLs, search terms or user names lives in the test files themselves.

Every value can be overridden with an environment variable, e.g.:

    HEADLESS=true DEVICE_NAME="iPhone 12 Pro" pytest
"""
import os
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "y")


# ---- Paths ---------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = ROOT_DIR / "screenshots"
LOG_DIR = ROOT_DIR / "logs"

# ---- Browser / device ----------------------------------------------------
# Default device for every test. Can be changed per run (--device) or per
# test (@pytest.mark.device("...")). Accepted values:
#   - any Chrome DevTools device name: "Pixel 7", "iPhone 12 Pro", ...
#   - "custom"  -> uses CUSTOM_DEVICE below
#   - "desktop" -> no mobile emulation (normal desktop Chrome)
DEVICE_NAME = os.getenv("DEVICE_NAME", "Pixel 7")

CUSTOM_DEVICE = {
    "deviceMetrics": {"width": 412, "height": 915, "pixelRatio": 2.625},
    "userAgent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
    ),
}

HEADLESS = _bool("HEADLESS", False)
BROWSER_LANG = os.getenv("BROWSER_LANG", "en-US")

# ---- Timeouts (seconds) --------------------------------------------------
IMPLICIT_WAIT = 0  # keep 0: the framework uses explicit waits only
EXPLICIT_WAIT = int(os.getenv("EXPLICIT_WAIT", "20"))
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "45"))
POPUP_WAIT = float(os.getenv("POPUP_WAIT", "3"))  # how long to keep looking for late popups
