import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture
def browser():
    options = Options()
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()
