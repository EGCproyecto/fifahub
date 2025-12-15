import os
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
GENERIC_CSV = os.path.join(DATA_DIR, "generic_sample.csv")
FIFA_CSV = os.path.join(DATA_DIR, "fifa_sample.csv")


def _login(driver, host):
    driver.get(f"{host}/login")
    time.sleep(4)
    email_field = driver.find_element(By.NAME, "email")
    password_field = driver.find_element(By.NAME, "password")
    email_field.send_keys("user1@example.com")
    password_field.send_keys("1234")
    password_field.send_keys(Keys.RETURN)
    time.sleep(4)


def _open_upload_form(driver, host):
    driver.get(f"{host}/tabular/upload")
    time.sleep(3)


def _submit_upload_form(driver, dataset_name, csv_path):
    name_field = driver.find_element(By.NAME, "name")
    name_field.clear()
    name_field.send_keys(dataset_name)
    file_input = driver.find_element(By.NAME, "csv_file")
    file_input.send_keys(csv_path)
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()


def _upload_valid_dataset(driver, host, dataset_name):
    _open_upload_form(driver, host)
    _submit_upload_form(driver, dataset_name, FIFA_CSV)
    time.sleep(4)
    current_url = driver.current_url.rstrip("/")
    dataset_id = current_url.split("/")[-1]
    return dataset_id


def test_tabular_upload_rejects_generic_csv():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        _login(driver, host)
        _open_upload_form(driver, host)
        _submit_upload_form(driver, "Generic CSV", GENERIC_CSV)
        time.sleep(3)

        if "ValidationError" not in driver.page_source:
            raise AssertionError("Validation error message not found for invalid CSV upload.")

    finally:
        close_driver(driver)


def test_tabular_upload_accepts_valid_fifa_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        _login(driver, host)
        _open_upload_form(driver, host)
        dataset_name = "FIFA Sample Dataset"
        _submit_upload_form(driver, dataset_name, FIFA_CSV)
        time.sleep(4)

        if "/tabular/" not in driver.current_url:
            raise AssertionError("Upload did not redirect to the tabular detail page.")

        header = driver.find_element(By.TAG_NAME, "h1")
        if dataset_name not in header.text:
            raise AssertionError("Dataset title was not rendered on the detail page.")

    finally:
        close_driver(driver)


def test_dataset_detail_has_no_flamapy_error_for_csv():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()
        _login(driver, host)
        dataset_id = _upload_valid_dataset(driver, host, "FIFA Detail Verification")

        driver.get(f"{host}/dataset/view/{dataset_id}")
        time.sleep(4)

        if "Internal Server Error" in driver.page_source or "HTTP 500" in driver.page_source:
            raise AssertionError("Dataset detail page shows an HTTP 500 error for Flamapy section.")

    except NoSuchElementException as exc:
        raise AssertionError("Expected elements were not found while verifying dataset detail.") from exc
    finally:
        close_driver(driver)


test_tabular_upload_rejects_generic_csv()
test_tabular_upload_accepts_valid_fifa_dataset()
test_dataset_detail_has_no_flamapy_error_for_csv()


def test_author_follow_toggle():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        _login(driver, host)

        author_id = 1
        driver.get(f"{host}/dataset/authors/{author_id}")
        time.sleep(3)

        btn = driver.find_element(By.ID, "author-follow-toggle")
        initial_text = btn.text.strip()

        btn.click()
        time.sleep(3)
        first_toggle_text = btn.text.strip()

        btn.click()
        time.sleep(3)
        second_toggle_text = btn.text.strip()

        if first_toggle_text == initial_text:
            raise AssertionError("Follow toggle did not change state on first click.")
        if second_toggle_text == first_toggle_text:
            raise AssertionError("Follow toggle did not revert on second click.")
    finally:
        close_driver(driver)


test_author_follow_toggle()
