import re
import time

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver


def wait_for_page_to_load(driver, timeout=6):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def wait_for_trending_items(driver, timeout=6):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "#trending-list a")) > 0
        or len(d.find_elements(By.ID, "trending-loading")) == 0
    )


def extract_trending_counts(driver):
    items = driver.find_elements(By.CSS_SELECTOR, "#trending-list .list-group-item a")
    results = {}
    for item in items:
        title_el = item.find_element(By.CSS_SELECTOR, ".fw-bold")
        count_el = item.find_element(By.CSS_SELECTOR, ".text-primary")
        title = title_el.text.strip()
        match = re.search(r"(\d+)", count_el.text)
        results[title] = int(match.group(1)) if match else 0
    return results


def test_trending_widget_visible():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        driver.get(f"{host}/")
        wait_for_page_to_load(driver)
        wait_for_trending_items(driver)
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


def test_trending_widget_updates_after_download():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()

        datasets_resp = requests.get(f"{host}/api/datasets-polymorphic", timeout=10)
        datasets_resp.raise_for_status()
        datasets = datasets_resp.json()
        assert datasets, "No datasets available for trending test"

        target = datasets[0]
        target_id = target["id"]
        target_title = target["title"] or f"Dataset {target_id}"

        driver.get(f"{host}/")
        wait_for_page_to_load(driver)
        wait_for_trending_items(driver)

        before_counts = extract_trending_counts(driver)
        assert target_title in before_counts, "Target dataset not visible in trending list"
        before_downloads = before_counts[target_title]

        download_resp = requests.get(f"{host}/dataset/download/{target_id}", timeout=15)
        assert download_resp.status_code == 200, f"Download endpoint failed with {download_resp.status_code}"
        time.sleep(1)

        driver.get(f"{host}/")
        wait_for_page_to_load(driver)
        wait_for_trending_items(driver)
        after_counts = extract_trending_counts(driver)

        assert after_counts.get(target_title) == before_downloads + 1, "Trending widget did not refresh downloads count"
    finally:
        close_driver(driver)


if __name__ == "__main__":
    test_trending_widget_visible()
