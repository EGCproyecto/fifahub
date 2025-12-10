import os
import time

import pytest

from core.environment.host import get_host_for_selenium_testing

# Tabular datasets for Selenium UI checks. Defaults come from the seeded data in this environment.
RELATED_DATASET_ID = os.getenv("TEST_DATASET_WITH_RECS_ID", "6")
NO_RELATED_DATASET_ID = os.getenv("TEST_DATASET_NO_RECS_ID", "7")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "user1@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "1234")


def _get_related_block(browser):
    # Card containing the "Related Datasets" header in the tabular detail template.
    return browser.find_element(
        "xpath", "//div[contains(@class,'card')][.//h4[contains(normalize-space(),'Related Datasets')]]"
    )


def _login(browser, host):
    browser.get(f"{host}/login")
    time.sleep(1)
    browser.find_element("name", "email").send_keys(TEST_USER_EMAIL)
    browser.find_element("name", "password").send_keys(TEST_USER_PASSWORD)
    submit = browser.find_element("css selector", "button[type='submit'],input[type='submit']")
    submit.click()
    time.sleep(2)


def test_related_datasets_block_visible(browser):
    host = get_host_for_selenium_testing()
    _login(browser, host)
    browser.get(f"{host}/tabular/{RELATED_DATASET_ID}")
    time.sleep(3)

    block = _get_related_block(browser)
    assert block.is_displayed()


def test_related_dataset_cards_render(browser):
    host = get_host_for_selenium_testing()
    _login(browser, host)
    browser.get(f"{host}/tabular/{RELATED_DATASET_ID}")
    time.sleep(3)

    block = _get_related_block(browser)
    cards = block.find_elements("css selector", "a.list-group-item-action")
    assert cards, "Expected at least one related dataset card"

    for card in cards:
        assert card.is_displayed()
        title_el = card.find_element("tag name", "h5")
        assert title_el.text.strip()
        href = card.get_attribute("href") or ""
        assert href, "Related dataset link should not be empty"
