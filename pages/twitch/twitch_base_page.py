"""
Things every Twitch page shares: the site's base URL and the popups Twitch shows.

Every Twitch page object inherits from this instead of BasePage directly.
"""
from selenium.webdriver.common.by import By

from framework.base_page import BasePage


class TwitchBasePage(BasePage):
    POPUP_LOCATORS = (
        # "Open in app / Continue in browser" bottom sheet on the mobile site:
        #   <a href="https://twitch.tv/?...open_in_app...">Open in App</a>
        #   <button>Continue in browser</button>   <- click this
        (By.XPATH, "//a[contains(@href, 'open_in_app')]/following-sibling::button[1]"),
    )
