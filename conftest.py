"""
Pytest fixtures and hooks shared by all tests, for any website.

Device selection, highest priority first:
  1. --device on the command line           pytest --device "iPhone 12 Pro"
  2. @pytest.mark.device("...") on a test   (a test that needs a specific device)
  3. DEVICE_NAME in config/settings.py      (default)

On failure, a screenshot is saved automatically and attached to the HTML report.
"""
import pytest

from config import settings
from framework.driver_factory import create_chrome_driver


def pytest_addoption(parser):
    group = parser.getgroup("browser")
    group.addoption("--device", action="store", default=None,
                    help='Device to emulate, e.g. "Pixel 7", "iPhone 12 Pro", "desktop"')
    group.addoption("--headless", action="store_true", default=None,
                    help="Run Chrome without a visible window")


def _device_for(request) -> str:
    cli = request.config.getoption("--device")
    if cli:
        return cli
    marker = request.node.get_closest_marker("device")
    if marker and marker.args:
        return marker.args[0]
    return settings.DEVICE_NAME


@pytest.fixture
def driver(request):
    """A fresh Chrome per test, always closed afterwards."""
    drv = create_chrome_driver(
        device_name=_device_for(request),
        headless=request.config.getoption("--headless"),
    )
    request.node._driver = drv
    yield drv
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    drv = getattr(item, "_driver", None)
    if drv is None:
        return
    settings.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in item.name)
    path = settings.SCREENSHOT_DIR / f"FAILED_{safe_name}.png"
    try:
        drv.save_screenshot(str(path))
    except Exception:  # browser may already be gone
        return
    try:
        import pytest_html
    except ImportError:
        return
    extras = getattr(report, "extras", [])
    extras.append(pytest_html.extras.image(str(path)))
    report.extras = extras
