import pytest

from pages.twitch import HomePage


@pytest.mark.twitch
@pytest.mark.device("Pixel 7")
def test_search_game_and_open_streamer(driver):
    """
        TC-001: Search for a game on Twitch (mobile) and open a streamer.
    """
    # ---- Test data -------------------------------------------------------------
    BASE_URL = "https://www.twitch.tv/"
    SEARCH_TERM = "StarCraft II"
    SCROLL_TIMES = 2
    STREAMER_INDEX = 0  # which streamer to pick among the ones visible after scrolling

    # 1. Go to Twitch
    home = HomePage(driver).load(BASE_URL)

    # 2. Click the search icon
    search = home.click_search_icon()

    # 3. Input the search term
    search.search(SEARCH_TERM)

    # 4. Click the Channels tab
    search.click_channels_tab()

    # 5. Scroll down
    search.scroll_down(times=SCROLL_TIMES)

    # 6. Select one streamer
    streamer = search.select_streamer(index=STREAMER_INDEX)

    # 7. Wait for the page to load and take a screenshot
    streamer.wait_until_loaded()
    screenshot = streamer.take_streamer_screenshot()

    # Assertions
    assert streamer.channel_name.lower() in driver.current_url.lower(), \
        f"Expected to be on channel '{streamer.channel_name}', got {driver.current_url}"
    assert screenshot.exists() and screenshot.stat().st_size > 0, "Screenshot was not saved"
