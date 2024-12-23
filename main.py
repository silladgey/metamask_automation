import getpass
import os
import shutil

import pyperclip
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from prompts import enter_password_text
from versions import SupportedVersions


def download_extension(version: str, directory: str):
    """
    Download the MetaMask extension for a specific version

    Args:
        version (str): Version of the MetaMask extension to download
    """
    url = f"https://github.com/MetaMask/metamask-extension/releases/download/v{version}/metamask-chrome-{version}.zip"

    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(f"{directory}/{version}.zip", "wb") as f:
            shutil.copyfileobj(response.raw, f)


def get_extension_id(driver: webdriver.Chrome) -> str:
    """
    Get the ID of the MetaMask extension

    Args:
        driver (webdriver.Chrome): Chrome WebDriver instance

    Returns:
        str: ID of the MetaMask extension
    """
    driver.get("chrome://extensions")

    extensions_manager = driver.find_element(
        By.TAG_NAME, "extensions-manager"
    ).shadow_root

    extensions_item_list = extensions_manager.find_element(
        By.CSS_SELECTOR, "extensions-item-list"
    )

    extensions_item = extensions_item_list.shadow_root.find_element(
        By.CSS_SELECTOR, "extensions-item"
    )

    extension_id = extensions_item.get_attribute("id")
    return extension_id


def setup_chrome_with_extension(
    extension_path: str, headless=False
) -> webdriver.Chrome:
    """
    Setup Chrome WebDriver with a custom extension

    Args:
        extension_path (str): Path to the Chrome extension (.crx file or unpacked extension directory)
        headless (bool): Whether to run Chrome in headless mode

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance
    """
    chrome_options = Options()

    # ? https://stackoverflow.com/questions/76818316/selenium-webdriver-doesnt-work-with-metamask
    if extension_path.endswith(".zip"):
        chrome_options.add_extension(extension_path)
    else:
        chrome_options.add_argument(f"--load-extension={extension_path}")

    if headless:
        chrome_options.add_argument("--headless=new")  # New headless mode for Chrome
        chrome_options.add_argument(
            "--window-size=1920,1080"
        )  # Set a default window size
    else:
        chrome_options.add_argument("--start-maximized")

    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-gpu")  # Required for some systems
    chrome_options.add_argument("--no-sandbox")  # Required for some Linux systems

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def click_element(driver: webdriver.Chrome, xpath: str):
    elem = driver.find_element(By.XPATH, xpath)
    elem.click()


def type_text(driver: webdriver.Chrome, xpath: str, text: str):
    elem = driver.find_element(By.XPATH, xpath)
    elem.send_keys(text)


def create_a_new_wallet(driver: webdriver.Chrome, password: str):
    wait = WebDriverWait(driver, timeout=10)

    button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/ul/li[2]/button"
    click_element(driver, button_xpath)

    wait.until(EC.url_contains("metametrics"))

    if "metametrics" in driver.current_url:
        button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/button[1]"
        click_element(driver, button_xpath)

    wait.until(EC.url_contains("create-password"))

    if "create-password" in driver.current_url:
        password_input_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/form/div[1]/label/input"
        type_text(driver, password_input_xpath, password)

        confirm_password_input_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/form/div[2]/label/input"
        type_text(driver, confirm_password_input_xpath, password)

        click_element(
            driver,
            "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/form/div[3]/label/span[1]/input",
        )

        button_xpath = (
            "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/form/button"
        )
        button = driver.find_element(By.XPATH, button_xpath)
        if button.is_enabled():
            button.click()

    wait.until(EC.url_contains("secure-your-wallet"))

    if "secure-your-wallet" in driver.current_url:
        xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/button[2]"  # yes by default
        click_element(driver, xpath)

    wait.until(EC.url_contains("review-recovery-phrase"))

    if "review-recovery-phrase" in driver.current_url:
        xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[6]/button"
        click_element(driver, xpath)

        xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[6]/div/div/a[2]"
        click_element(driver, xpath)

        recovery_phrase = pyperclip.paste()
        print(f"Recovery Phrase: {recovery_phrase}")

        # TODO Save the recovery phrase somewhere safe
        xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[6]/div/button"
        click_element(driver, xpath)

    wait.until(EC.url_contains("confirm-recovery-phrase"))

    if "confirm-recovery-phrase" in driver.current_url:
        recovery_words = recovery_phrase.split()

        # ! JavaScript is inevitable
        recovery_script = """
        const recoveryWords = arguments[0];
        const recoveryInputs = document.querySelectorAll("input[data-testid^='recovery-phrase-input-']");
        recoveryWords.forEach((word, index) => {
            const input = Array.from(recoveryInputs).find(input => input.dataset.testid.endsWith(`-${index}`));
            if (input) {
                input.setAttribute('value', word);
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
        """
        driver.execute_script(recovery_script, recovery_words)

        button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[5]/button"

        button = driver.find_element(By.XPATH, button_xpath)
        button.click()

    wait.until(EC.url_contains("completion"))

    if "completion" in driver.current_url:
        button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[3]/button"
        click_element(driver, button_xpath)

        wait.until(EC.url_contains("pin-extension"))

        button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/button"
        click_element(driver, button_xpath)
        button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/button"
        click_element(driver, button_xpath)


def import_an_existing_wallet(driver: webdriver.Chrome):
    button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/ul/li[3]/button"
    click_element(driver, button_xpath)


def import_private_key(driver: webdriver.Chrome, private_key: str):
    pass


def onboard(driver: webdriver.Chrome):
    extension_id = get_extension_id(driver)
    extension_url = f"chrome-extension://{extension_id}/home.html"

    wait = WebDriverWait(driver, timeout=10)
    wait.until(lambda driver: len(driver.window_handles) > 1)

    all_tabs = driver.window_handles

    print(f"There are {len(all_tabs)} tabs open")
    for index, tab in enumerate(all_tabs):
        driver.switch_to.window(tab)
        print(f"Tab {index + 1}: {driver.title}")

    for tab in all_tabs:
        if extension_url not in driver.current_url:
            driver.switch_to.window(tab)
            print(driver.current_url)

    driver.get(extension_url)

    wait.until(
        lambda driver: driver.execute_script("return document.readyState == 'complete'")
    )

    print("Onboarding...")

    password = getpass.getpass(enter_password_text)
    while len(password) < 8:
        print("Password must be at least 8 characters long")
        password = getpass.getpass(enter_password_text)

    click_element(driver, "//*[@id='onboarding__terms-checkbox']")

    create_a_new_wallet(driver, password)


def main():
    extension_dir = os.path.join(os.getcwd(), "extension")
    extension_path = os.path.join(
        extension_dir, f"{SupportedVersions.LATEST_VERSION}.zip"
    )

    if not os.path.exists(extension_path):
        print("Downloading MetaMask extension...")
        download_extension(SupportedVersions.LATEST_VERSION, extension_dir)

    extension_path = os.path.abspath(
        f"extension/{SupportedVersions.LATEST_VERSION}.zip"
    )

    driver = setup_chrome_with_extension(extension_path)

    onboard(driver)
    input("Press Enter to close the browser...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        quit()
