"""Twitch home page (mobile layout)."""
from selenium.webdriver.common.by import By

from pages.twitch.search_page import SearchPage
from pages.twitch.twitch_base_page import TwitchBasePage


class HomePage(TwitchBasePage):

    SEARCH_ICON = (
        By.XPATH,
        "//a[@href='/directory'][following-sibling::a[1][@href='/activity']]",
    )

    def load(self, base_url: str) -> "HomePage":
        self.open(base_url)
        # The "Open in app or stay using browser?" popup appears
        closed = self.dismiss_popups()
        self.log.info("Popups closed on home page: %d", closed)
        return self

    def click_search_icon(self, timeout: float = 10) -> SearchPage:
        """Click the search icon. Fails the test if it can't be found."""
        self.log.info("Clicking search icon")
        icon = self.wait_clickable(
            self.SEARCH_ICON, timeout=timeout,
            message="Search icon not found",
        )
        self.click(icon, name="search icon")
        return SearchPage(self.driver)
