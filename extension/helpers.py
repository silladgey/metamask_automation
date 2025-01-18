import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from storage.extension import ExtensionStorage

from utils.enums.developer_mode import DevModeState


def get_extension_home_url() -> str:
    storage = ExtensionStorage()
    extension_url = storage.get_extension_base_url("metamask")
    return extension_url + "/home.html"


def run_script(driver: webdriver, file_name: str, args: dict = None) -> any:
    """
    Run a JavaScript script in the browser using a Selenium WebDriver.

    Args:
        driver (webdriver): The Selenium WebDriver instance controlling the browser.
        path (str): The path to the JavaScript file to run.
        args (dict): The arguments to pass to the script.
    Returns:
        any: The result of the script execution.
    """
    with open(
        os.path.join(os.getcwd(), "scripts", file_name), "r", encoding="utf-8"
    ) as f:
        script = f.read()
    if args:
        result = driver.execute_script(script, *args.values())
    else:
        result = driver.execute_script(script)
    return result


def toggle_developer_mode(locator: WebElement, to: DevModeState) -> bool:
    """
    Enable developer mode in the MetaMask extension.

    Args:
        locator (WebElement): The WebElement to locate the developer mode trigger
        to (DevModeState): The state to set the developer mode to
    Returns:
        bool: The state of the developer mode after toggling
    """
    wait = WebDriverWait(locator, 100)
    developer_mode_trigger = wait.until(
        EC.presence_of_element_located((By.ID, "devMode"))
    )

    is_dev_mode_enabled = developer_mode_trigger.get_attribute("checked")

    if to == DevModeState.OFF and not is_dev_mode_enabled:  # ? 00
        return False
    if to == DevModeState.ON and is_dev_mode_enabled:  # ? 11
        return True
    if to == DevModeState.OFF and is_dev_mode_enabled:  # ? 01
        developer_mode_trigger.click()
        return False
    if to == DevModeState.ON and not is_dev_mode_enabled:  # ? 10
        developer_mode_trigger.click()
        return True
    if to not in DevModeState.__members__:  # ? default
        raise ValueError(f"Invalid developer mode state: {to}")
