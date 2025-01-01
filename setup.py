import os
import shutil
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.remote.webelement import WebElement

from utils.enums.developer_mode import DevModeState
from utils.enums.metamask_extension import SupportedVersion

from storage.extension import ExtensionStorage

EXTENSION_DIR = os.path.join(os.getcwd(), "extension")


def download_metamask_zip(version: str) -> None:
    """
    Download the MetaMask extension for a specific version

    Args:
        version (str): Version of the MetaMask extension to download
    Returns:
        None
    """

    url = f"https://github.com/MetaMask/metamask-extension/releases/download/v{version}/metamask-chrome-{version}.zip"
    print(f"Retrieving MetaMask version {version} extension from {url}")

    extension_path = os.path.join(EXTENSION_DIR, f"{version}.zip")

    if not os.path.exists(EXTENSION_DIR):
        # ? Create the extension directory if it doesn't exist
        os.makedirs(EXTENSION_DIR, exist_ok=True)

    if os.path.exists(extension_path):
        # ? Skip downloading if the extension already exists
        print(
            f"MetaMask version {version} extension already exists at location {extension_path}"
        )
        return

    with requests.get(url, stream=True, timeout=100) as response:
        # ? Download the extension
        response.raise_for_status()
        with open(extension_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)


def load_extension_from_file(version: str) -> str:
    """
    Load an extension from a file.

    Args:
        version (str): Version of the extension to load.
    Returns:
        str: Path to the installed extension.
    """
    # ? Path: extension/{VERSION}.crx
    installed_extension_path = os.path.abspath(
        os.path.join(EXTENSION_DIR, f"{version}.crx")
    )

    if not os.path.exists(installed_extension_path):
        # ? Path: extension/{VERSION}_0.crx
        crx_files = [f for f in os.listdir(EXTENSION_DIR) if f.endswith(".crx")]
        version_files = [f for f in crx_files if f.startswith(version)]

        if version_files:
            highest_version_file = max(
                version_files, key=lambda x: int(x.split("_")[-1].split(".")[0])
            )
            installed_extension_path = os.path.abspath(
                os.path.join(EXTENSION_DIR, highest_version_file)
            )

    if not os.path.exists(installed_extension_path):
        # ? Path: extension/{VERSION}.zip
        installed_extension_path = os.path.abspath(
            os.path.join(EXTENSION_DIR, f"{version}.zip")
        )

    if not os.path.exists(installed_extension_path):
        # ? Download the MetaMask extension
        download_metamask_zip(version)

    if not os.path.exists(installed_extension_path):
        # ? Raise an error if the extension is not found
        raise FileNotFoundError(
            f"MetaMask extension not found at location {installed_extension_path}"
        )

    print(f"Loaded extension from {installed_extension_path}")
    return installed_extension_path


def setup_chrome_driver_for_metamask(
    options: webdriver.ChromeOptions,
    service: webdriver.ChromeService,
    metamask_version: str = SupportedVersion.LATEST,
    headless=False,
) -> webdriver.Chrome:
    """
    Setup Chrome WebDriver with a custom MetaMask extension.

    Args:
        options (webdriver.ChromeOptions): Chrome options to configure the WebDriver.
        service (webdriver.ChromeService): Chrome service to manage the WebDriver.
        metamask_version (str, optional): Version of the MetaMask extension to use. Defaults to SupportedVersion.LATEST.
        headless (bool, optional): Whether to run Chrome in headless mode. Defaults to False.
    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.
    Raises:
        FileNotFoundError: If the MetaMask extension file is not found.
    Notes:
        - The function downloads the latest MetaMask extension and configures the Chrome WebDriver to use it.
        - Supports both .crx and .zip extension formats.
        - Adds necessary Chrome options for headless mode and disables notifications and GPU.
    """
    extension_path = load_extension_from_file(metamask_version)

    chrome_options = options
    chrome_options.add_extension(extension_path)

    if headless:
        # ? New headless mode for Chrome
        chrome_options.add_argument("--headless=new")
        # ? Set a default window size
        chrome_options.add_argument("--window-size=1024,716")

    chrome_options.add_argument("--disable-notifications")  # ? Disable notifications
    chrome_options.add_argument("--disable-gpu")  # ? Required for some systems
    chrome_options.add_argument("--no-sandbox")  # ? Required for some Linux systems

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_chrome_extensions_manager(locator: WebElement) -> ShadowRoot:
    """
    Get the Chrome extensions manager from the browser.

    Args:
        locator (WebElement): The WebElement to locate the extensions manager
    Returns:
        ShadowRoot: The shadow root of the extensions manager
    """
    wait = WebDriverWait(locator, 100)

    extensions_manager = wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "extensions-manager"))
    )
    return extensions_manager.shadow_root


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


def run_script(driver: webdriver, file_name: str, args: dict) -> any:
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


def get_extension_id(driver: webdriver, storage, extension_name: str) -> str:
    """
    Finds the MetaMask extension ID in the browser using a Selenium WebDriver.
    Args:
        driver (webdriver): The Selenium WebDriver instance controlling the browser.
        extension_name (str): The name of the extension to find the ID for.
    Returns:
        str: The ID of the MetaMask extension.
    Raises:
        Exception: If the MetaMask extension is not found.
    """

    extensions_url = None
    if "chrome" in driver.capabilities["browserName"].lower():
        extensions_url = "chrome://extensions/"
        driver.get(extensions_url)
    else:
        raise Exception("This function is designed to work with Chrome browser only")

    wait = WebDriverWait(driver, 100)
    wait.until(EC.url_to_be(extensions_url))

    extensions_manager = get_chrome_extensions_manager(driver)
    extensions_toolbar = extensions_manager.find_element(By.ID, "toolbar")

    toggle_developer_mode(extensions_toolbar.shadow_root, DevModeState.ON)

    extensions_item_list = extensions_manager.find_element(
        By.CSS_SELECTOR, "extensions-item-list"
    )

    extensions_items = extensions_item_list.shadow_root.find_elements(
        By.CSS_SELECTOR, "extensions-item"
    )

    for item in extensions_items:
        ext_name = item.shadow_root.find_element(By.ID, "name")

        if extension_name in ext_name.text:
            extension_id = item.get_attribute("id")
            storage.store_extension(
                extension_name.lower(), {"extension_id": extension_id}
            )
            return extension_id

    raise Exception("Extension not found")


if __name__ == "__main__":
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    options = Options()
    service = Service()
    storage = ExtensionStorage()

    driver = setup_chrome_driver_for_metamask(
        options=options,
        service=service,
        metamask_version=SupportedVersion.LATEST,
        headless=False,
    )

    metamask_extension_id = get_extension_id(driver, storage, "MetaMask")
    print(f"MetaMask extension ID: {metamask_extension_id}")

    driver.quit()
