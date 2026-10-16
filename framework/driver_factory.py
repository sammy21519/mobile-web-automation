"""
Creates Chrome WebDriver instances, with or without mobile emulation.

Selenium 4.6+ includes Selenium Manager, which finds or downloads a
ChromeDriver that matches your installed Chrome, so no driver setup is needed.
"""
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config import settings
from framework.logger import get_logger

log = get_logger(__name__)

DESKTOP = "desktop"
CUSTOM = "custom"


def _mobile_emulation(device_name: str) -> Optional[dict]:
    """Return the Chrome mobileEmulation setting for a device, or None for desktop."""
    name = (device_name or "").strip()
    if name.lower() == DESKTOP:
        return None
    if name.lower() == CUSTOM or not name:
        return settings.CUSTOM_DEVICE
    return {"deviceName": name}


def create_chrome_driver(
    device_name: Optional[str] = None,
    headless: Optional[bool] = None,
    lang: Optional[str] = None,
) -> webdriver.Chrome:
    """
    Build a Chrome driver.

    Any argument left as None falls back to config/settings.py, so callers only
    pass what they actually want to change.
    """
    device_name = settings.DEVICE_NAME if device_name is None else device_name
    headless = settings.HEADLESS if headless is None else headless
    lang = lang or settings.BROWSER_LANG

    options = Options()
    emulation = _mobile_emulation(device_name)
    if emulation:
        options.add_experimental_option("mobileEmulation", emulation)

    options.add_argument(f"--lang={lang}")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option(
        "prefs",
        {
            "profile.default_content_setting_values.notifications": 2,
            # Ask websites for pages in this language (Accept-Language header),
            # so text-based locators are predictable regardless of the OS language.
            "intl.accept_languages": f"{lang},en",
        },
    )

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    if headless or not emulation:
        options.add_argument("--window-size=600,1000" if emulation else "--window-size=1280,1000")

    log.info("Starting Chrome (device=%s, headless=%s, lang=%s)", device_name, headless, lang)
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(settings.IMPLICIT_WAIT)
    driver.set_page_load_timeout(settings.PAGE_LOAD_TIMEOUT)
    return driver
