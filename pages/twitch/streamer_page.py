"""Twitch streamer/channel page (mobile layout)."""
from pathlib import Path

from selenium.webdriver.common.by import By

from pages.twitch.twitch_base_page import TwitchBasePage


class StreamerPage(TwitchBasePage):
    # Channel without videos: the title of the empty-state block that sits right
    # after the channel tabs, inside the page's main content:
    #   <main id="page-main-content-wrapper">
    #     <div>
    #       <div> <div class="... tw-tabs"> ... <ul role="tablist"> </div> </div>
    #       <div>                                              <- empty-state block
    #         <div> <div class="... tw-svg"><svg/></div> </div>   <- icon
    #         <div> <p class="... tw-title">此頻道沒有內容。</p> </div>   <- target
    #         <p>好安靜...實在太安靜了</p>
    # Only the stable id and Twitch's tw-* design classes are used, never the
    # generated ones like "Layout-sc-1xcs6mc-0" or "cwkUIP".
    NO_VIDEO = (
        By.XPATH,
        "//main[@id='page-main-content-wrapper']"
        "//div[contains(@class, 'tw-tabs')]/parent::div"
        "/following-sibling::div[1][.//div[contains(@class, 'tw-svg')]]"
        "//p[contains(@class, 'tw-title')]",
    )

    # Channel with videos: a real thumbnail inside a video card:
    #   <button role="link"> ... <img src="https://static-cdn.jtvnw.net/..."> </button>
    VIDEO_THUMBNAIL = (By.CSS_SELECTOR, "button[role='link'] img[src*='https']")

    # True once every thumbnail on screen has downloaded. An <img> gets its src
    # immediately but stays black until the picture arrives, so "has a src" isn't enough.
    _THUMBNAILS_ON_SCREEN_LOADED_JS = """
        const onScreen = [...document.querySelectorAll(arguments[0])].filter(img => {
            const r = img.getBoundingClientRect();
            return r.bottom > 0 && r.top < window.innerHeight
                && r.right > 0 && r.left < window.innerWidth;
        });
        return onScreen.length > 0
            && onScreen.every(img => img.complete && img.naturalWidth > 0);
    """

    def __init__(self, driver, channel_name: str):
        super().__init__(driver)
        self.channel_name = channel_name

    def wait_until_loaded(self) -> str:
        """
        Wait until the channel page shows its content and return which kind:
          "no_video"   - the channel's "no content" message is showing
          "with_video" - video thumbnails are showing and the ones on screen have loaded
        """
        self.log.info("Waiting for streamer page '%s' to load", self.channel_name)
        self.wait_for_url_contains(self.channel_name)
        self.wait_for_document_ready()

        # no_video is listed first since it shows sooner
        state = self.wait_for_any(
            {"no_video": self.NO_VIDEO, "with_video": self.VIDEO_THUMBNAIL},
            message=f"Channel '{self.channel_name}' showed neither 'no content' nor a video thumbnail",
        )
        if state == "with_video":
            self.wait.until(
                lambda d: d.execute_script(self._THUMBNAILS_ON_SCREEN_LOADED_JS,
                                           self.VIDEO_THUMBNAIL[1]),
                message=f"Video thumbnails on channel '{self.channel_name}' did not finish loading",
            )
        self.log.info("Channel '%s' loaded: %s", self.channel_name, state)
        return state

    def take_streamer_screenshot(self) -> Path:
        return self.take_screenshot(f"streamer_{self.channel_name}")
