import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=6):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def test_trending_widget_visible():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/")
        wait_for_page_to_load(driver)
        time.sleep(1)

        heading = driver.find_element(By.XPATH, "//h2[normalize-space()='Trending Datasets']")
        assert heading.is_displayed(), "Trending heading not visible on home page"

        cards = driver.find_elements(By.CSS_SELECTOR, "#trending-list a")
        assert len(cards) >= 1, "No trending items rendered"

        first = cards[0]
        href = first.get_attribute("href")
        assert href and ("/doi/" in href or "/dataset/" in href), "Trending link does not point to dataset detail"

    finally:
        close_driver(driver)


if __name__ == "__main__":
    test_trending_widget_visible()
