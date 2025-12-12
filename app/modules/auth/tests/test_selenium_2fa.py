import os
import time
import uuid

import pyotp
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.environment.host import get_host_for_selenium_testing
from core.locust.common import get_csrf_token
from core.selenium.common import close_driver, initialize_driver

HOST = get_host_for_selenium_testing().rstrip("/")
DEFAULT_NAME = "Selenium"
DEFAULT_SURNAME = "Tester"
RUN_SELENIUM = os.getenv("RUN_SELENIUM_TESTS", "false").lower() == "true"
pytestmark = pytest.mark.skipif(not RUN_SELENIUM, reason="Set RUN_SELENIUM_TESTS=true to run Selenium UI tests")


@pytest.fixture
def driver():
    driver = initialize_driver()
    driver.implicitly_wait(5)
    yield driver
    close_driver(driver)


def _create_test_user():
    session = requests.Session()
    email = f"selenium+{uuid.uuid4().hex}@example.com"
    password = f"S3cure-{uuid.uuid4().hex[:6]}"
    response = session.get(f"{HOST}/signup/")
    csrf_token = get_csrf_token(response)
    signup = session.post(
        f"{HOST}/signup/",
        data={
            "name": DEFAULT_NAME,
            "surname": DEFAULT_SURNAME,
            "email": email,
            "password": password,
            "csrf_token": csrf_token,
        },
        allow_redirects=False,
    )
    if signup.status_code not in (200, 302, 303):
        raise AssertionError(f"Unable to create test user: {signup.status_code}")
    session.get(f"{HOST}/logout")
    return email, password


def _enable_two_factor_via_api(email: str, password: str):
    session = requests.Session()
    response = session.get(f"{HOST}/login")
    csrf_token = get_csrf_token(response)
    login = session.post(
        f"{HOST}/login",
        data={"email": email, "password": password, "csrf_token": csrf_token},
        allow_redirects=True,
    )
    if login.status_code not in (200, 302, 303):
        raise AssertionError(f"Unable to authenticate test user: {login.status_code}")
    setup = session.post(f"{HOST}/2fa/setup")
    setup.raise_for_status()
    secret = setup.json()["secret"]
    code = pyotp.TOTP(secret).now()
    verify = session.post(f"{HOST}/2fa/verify-setup", json={"code": code})
    verify.raise_for_status()
    recovery_codes = verify.json()["recovery_codes"]
    session.get(f"{HOST}/logout")
    return secret, recovery_codes


def _login_with_credentials(driver, email, password):
    driver.get(f"{HOST}/logout")
    driver.get(f"{HOST}/login")
    email_input = driver.find_element(By.NAME, "email")
    password_input = driver.find_element(By.NAME, "password")
    email_input.clear()
    email_input.send_keys(email)
    password_input.clear()
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)


def _wait_for_two_factor_page(driver):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-two-factor-page]")))


def _submit_totp_code(driver, code: str):
    code_input = driver.find_element(By.ID, "twoFactorCodeInput")
    code_input.clear()
    code_input.send_keys(code)
    driver.find_element(By.CSS_SELECTOR, "#twoFactorTotpForm button[type='submit']").click()


def _complete_totp_challenge(driver, secret: str):
    _wait_for_two_factor_page(driver)
    otp = pyotp.TOTP(secret).now()
    _submit_totp_code(driver, otp)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//h1[contains(@class,'h2') and contains(normalize-space(),'Latest datasets')]",
            )
        )
    )


def test_enable_two_factor_from_settings(driver):
    email, password = _create_test_user()
    _login_with_credentials(driver, email, password)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='/logout']")))
    driver.get(f"{HOST}/2fa/settings")
    start_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "startSetupBtn")))
    start_button.click()
    secret_value = WebDriverWait(driver, 10).until(
        lambda drv: drv.find_element(By.ID, "secretField").get_attribute("value")
    )
    assert secret_value, "Secret field should be populated after clicking enable"
    totp_input = driver.find_element(By.ID, "totpInput")
    totp_input.clear()
    totp_input.send_keys(pyotp.TOTP(secret_value).now())
    driver.find_element(By.ID, "verifyCodeBtn").click()
    badge = WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.ID, "twoFactorStatus"), "Enabled")
    )
    assert badge is True


def test_login_prompts_for_two_factor_and_shows_error(driver):
    email, password = _create_test_user()
    _enable_two_factor_via_api(email, password)
    _login_with_credentials(driver, email, password)
    _wait_for_two_factor_page(driver)
    _submit_totp_code(driver, "000000")
    error = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-error-target='totp']"))
    )
    assert "Unable to verify" in error.text


def test_login_with_valid_totp_succeeds(driver):
    email, password = _create_test_user()
    secret, _ = _enable_two_factor_via_api(email, password)
    _login_with_credentials(driver, email, password)
    _complete_totp_challenge(driver, secret)


def test_login_with_recovery_code(driver):
    email, password = _create_test_user()
    secret, recovery_codes = _enable_two_factor_via_api(email, password)
    assert recovery_codes, "Recovery codes should exist after enabling 2FA"
    _login_with_credentials(driver, email, password)
    _wait_for_two_factor_page(driver)
    driver.find_element(By.CSS_SELECTOR, "[data-toggle-recovery]").click()
    recovery_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "recoveryCodeInput")))
    recovery_input.send_keys(recovery_codes.pop())
    driver.find_element(By.CSS_SELECTOR, "#recoveryCodeForm button[type='submit']").click()
    WebDriverWait(driver, 10).until(EC.url_contains("/"))


def test_disable_two_factor_from_ui(driver):
    email, password = _create_test_user()
    secret, _ = _enable_two_factor_via_api(email, password)
    _login_with_credentials(driver, email, password)
    _complete_totp_challenge(driver, secret)
    driver.get(f"{HOST}/2fa/settings")
    disable_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "disable2faBtn")))
    disable_button.click()
    password_input = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "disablePasswordInput")))
    password_input.send_keys(password)
    driver.find_element(By.ID, "confirmDisableBtn").click()
    WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.ID, "twoFactorStatus"), "Disabled"))
