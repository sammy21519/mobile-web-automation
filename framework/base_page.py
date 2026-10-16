"""
BasePage: website-independent actions shared by every Page Object.

Page Objects describe *what* is on a page (locators + page actions).
BasePage knows *how* to wait, click, type, scroll, close popups and take
screenshots - for any website.

Site-specific behaviour (which popups a site shows ...) goes in
a site base class such as pages/twitch/twitch_base_page.py, which overrides
POPUP_LOCATORS.
"""
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import settings
from framework.logger import get_logger

Locator = Tuple[str, str]


class BasePage:
    POPUP_LOCATORS: Sequence[Locator] = ()

    def __init__(self, driver: WebDriver, timeout: int = settings.EXPLICIT_WAIT):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.log = get_logger(self.__class__.__name__)

    # ---------- navigation ----------
    def open(self, url: str) -> None:
        self.log.info("Opening %s", url)
        self.driver.get(url)
        self.wait_for_document_ready()

    # ---------- waits ----------
    def _waiter(self, timeout: Optional[float]) -> WebDriverWait:
        return WebDriverWait(self.driver, timeout or self.timeout)

    def wait_for_document_ready(self, timeout: Optional[float] = None) -> None:
        self._waiter(timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def wait_for_url_contains(self, text: str, timeout: Optional[float] = None) -> None:
        self._waiter(timeout).until(
            lambda d: text.lower() in d.current_url.lower(),
            message=f"URL did not contain '{text}'",
        )

    def wait_visible(self, locator: Locator, timeout: Optional[float] = None, message: str = "") -> WebElement:
        """Wait for an element to be visible. `message` is shown if it times out."""
        return self._waiter(timeout).until(
            EC.visibility_of_element_located(locator),
            message=message or f"Element not visible: {locator}",
        )

    def wait_clickable(self, locator: Locator, timeout: Optional[float] = None, message: str = "") -> WebElement:
        """Wait for an element to be clickable. `message` is shown if it times out."""
        return self._waiter(timeout).until(
            EC.element_to_be_clickable(locator),
            message=message or f"Element not clickable: {locator}",
        )

    def wait_for_any(self, locators: Dict[str, Locator], timeout: Optional[float] = None,
                     message: str = "") -> str:
        """
        Wait until any of the named locators is visible and return its name, e.g.
            wait_for_any({"no_video": NO_VIDEO, "with_video": VIDEO_THUMBNAIL}) -> "no_video"

        All locators are checked on every poll, so whichever appears first wins.
        If several are visible on the same poll, the one listed first wins.
        """
        def _first_visible(driver):
            for name, locator in locators.items():
                for el in driver.find_elements(*locator):
                    try:
                        if el.is_displayed():
                            return name
                    except StaleElementReferenceException:
                        continue  # re-rendered mid-check; the next poll sees the new one
            return False

        expected = ", ".join(f"{name} {loc}" for name, loc in locators.items())
        state = self._waiter(timeout).until(
            _first_visible, message=message or f"None of these appeared: {expected}")
        self.log.info("Page state: %s", state)
        return state

    # ---------- actions ----------
    def click(self, element: WebElement, name: str = "element") -> None:
        """
        Click like a real user (a real pointer/touch event at the element's
        position).  `name` describes the element in log and failure messages.
        """
        self.scroll_into_view(element)
        try:
            element.click()
        except ElementClickInterceptedException as exc:
            # Selenium's message names the element that would receive the click
            self.log.error("Could not click %s: another element is covering it. %s",
                           name, (exc.msg or "").strip())
            raise
        except ElementNotInteractableException as exc:
            self.log.error("Could not click %s: it is not interactable (hidden, zero-size "
                           "or disabled). %s", name, (exc.msg or "").strip())
            raise
        except StaleElementReferenceException:
            self.log.error("Could not click %s: it was removed from the page "
                           "(the page re-rendered after it was found)", name)
            raise
        self.log.info("Clicked %s", name)

    def type_text(self, element: WebElement, text: str, clear: bool = True, submit: bool = False) -> None:
        if clear:
            element.clear()
        element.send_keys(text)
        if submit:
            element.send_keys(Keys.ENTER)

    def scroll_into_view(self, element: WebElement) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element
        )

    def scroll_down(self, times: int = 1, pause: float = 1.0, fraction: float = 0.8) -> None:
        """Scroll `fraction` of the viewport per step, like a user swiping up on a phone."""
        for i in range(times):
            self.driver.execute_script("window.scrollBy(0, window.innerHeight * arguments[0]);", fraction)
            self.log.info("Scrolled down (%d/%d)", i + 1, times)
            time.sleep(pause)  # let lazy-loaded content render

    def is_in_viewport(self, element: WebElement) -> bool:
        return self.driver.execute_script(
            "const r = arguments[0].getBoundingClientRect();"
            "return r.top >= 0 && r.bottom <= window.innerHeight;", element)

    # ---------- popups ----------
    def dismiss_popups(self, timeout: float = settings.POPUP_WAIT) -> int:
        """
        Close any popup listed in POPUP_LOCATORS. Popups often slide in a moment
        after a page loads, so this keeps checking for up to `timeout` seconds and
        stops once it has closed something and nothing else is showing.
        Returns how many popups were closed.
        """
        if not self.POPUP_LOCATORS:
            return 0
        closed, rounds_with_closes = 0, 0
        end = time.time() + timeout
        while time.time() < end:
            n = self._close_visible_popups()
            closed += n
            if n:
                rounds_with_closes += 1
                if rounds_with_closes >= 5:  # a "popup" that never goes away - stop
                    break
                time.sleep(0.5)  # let the closing animation finish, then re-check
                continue
            if closed:
                break
            time.sleep(0.3)
        return closed

    def _close_visible_popups(self) -> int:
        closed = 0
        for loc in self.POPUP_LOCATORS:
            for el in self.driver.find_elements(*loc):
                try:
                    showing = el.is_displayed() and el.is_enabled()
                except StaleElementReferenceException:
                    continue  # popup disappeared while we were checking it
                if showing:
                    self.click(el, name=f"popup close button {loc[1]}")
                    closed += 1
        return closed

    # ---------- screenshots ----------
    def take_screenshot(self, name: str) -> Path:
        """Save a PNG to screenshots/<name>_<timestamp>.png and return its path."""
        settings.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "screenshot"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = settings.SCREENSHOT_DIR / f"{safe_name}_{stamp}.png"
        self.driver.save_screenshot(str(path))
        self.log.info("Screenshot saved: %s", path)
        return path
