"""Twitch search input + search results (mobile layout)."""
from typing import List
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.twitch.twitch_base_page import TwitchBasePage


class SearchPage(TwitchBasePage):
    SEARCH_INPUT = (By.CSS_SELECTOR, "input[type='search']")

    # Result tabs (Top / Channels / Categories / ...)
    RESULT_TABS = (By.CSS_SELECTOR, "ul[role='tablist']")
    CHANNELS_TAB = (By.CSS_SELECTOR, "ul[role='tablist'] > li:nth-of-type(2) > a[href$='type=channels']")

    # Streamer cards in the results list
    STREAMER_LINKS = (By.CSS_SELECTOR, "div[role='list'] > div > a[href]")

    def search(self, term: str) -> "SearchPage":
        self.log.info("Searching for '%s'", term)
        box = self.wait_clickable(self.SEARCH_INPUT,
                                  message="Search input <input type='search'> not found")
        self.click(box, name="search input")
        self.type_text(box, term, submit=True)
        self.wait_visible(self.RESULT_TABS, message="Search results (result tabs) did not appear")
        return self

    def click_channels_tab(self) -> "SearchPage":
        self.log.info("Clicking the Channels tab")
        tab = self.wait_clickable(
            self.CHANNELS_TAB,
            message="Channels tab not found: expected <a href='...type=channels'> "
                    "in the 2nd <li> of <ul role='tablist'>",
        )
        self.click(tab, name="Channels tab")
        self.wait.until(lambda d: tab.get_attribute("aria-selected") == "true",
                        message="Channels tab did not become selected")
        self.wait_for_streamers()
        return self

    def wait_for_streamers(self) -> None:
        self.wait.until(lambda d: len(self.streamer_links()) > 0,
                        message="No streamers appeared in the results list (div[role='list'] > div > a[href])")

    def streamer_links(self) -> List[WebElement]:
        """Visible streamer links in the results list, in page order."""
        return [a for a in self.driver.find_elements(*self.STREAMER_LINKS) if a.is_displayed()]

    def select_streamer(self, index: int = 0):
        """
        Click a streamer. `index` counts among the streamers currently in the
        viewport (all streamers if none are in view).
        """
        from pages.twitch.streamer_page import StreamerPage  # avoid circular import

        links = self.streamer_links()
        assert links, "No streamers found in the results list"
        candidates = [a for a in links if self.is_in_viewport(a)] or links
        link = candidates[min(index, len(candidates) - 1)]

        channel = urlparse(link.get_attribute("href")).path.strip("/").split("/")[0]
        self.log.info("Selecting streamer '%s'", channel)
        self.click(link, name=f"streamer '{channel}'")
        return StreamerPage(self.driver, channel_name=channel)
