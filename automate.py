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

from utils.constants.prompts import ENTER_PASSWORD_TEXT
from utils.enums.metamask_extension import SupportedVersions


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
            "--window-size=1024,716"
        )  # Set a default window size

    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-gpu")  # Required for some systems
    chrome_options.add_argument("--no-sandbox")  # Required for some Linux systems

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


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


def get_extension_url(driver: webdriver.Chrome) -> str:
    extension_id = get_extension_id(driver)
    extension_url = f"chrome-extension://{extension_id}/home.html"
    return extension_url


# def go_to_extension_home(driver: webdriver.Chrome) -> str:
#     driver.get(extension_url)


def click_element(driver: webdriver.Chrome, xpath: str):
    elem = driver.find_element(By.XPATH, xpath)
    if elem:
        elem.click()


def type_text(driver: webdriver.Chrome, xpath: str, text: str):
    elem = driver.find_element(By.XPATH, xpath)
    if elem:
        elem.send_keys(text)


def type_onboarding_recovery_phrase(driver: webdriver.Chrome, recovery_phrase: str):
    """
    ! JavaScript is inevitable
    """
    recovery_words = recovery_phrase.split()

    recovery_script = """
    const recoveryWords = arguments[0];
    const recoveryInputs = document
        .querySelectorAll("input[data-testid^='recovery-phrase-input-']");
    recoveryWords.forEach((word, index) => {
        const input = Array
            .from(recoveryInputs)
            .find(input => input.dataset.testid.endsWith(`-${index}`)
        );
        if (input) {
            input.setAttribute('value', word);
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
    """
    driver.execute_script(recovery_script, recovery_words)


def close_home_onboarding_popup(driver: webdriver.Chrome) -> bool:
    """
    ! JavaScript is inevitable
    """
    return driver.execute_script(
        """
        const onboardingPopup = document
            .querySelector('.eth-overview__balance')
            .querySelector('[role="tooltip"]');
        if (onboardingPopup && onboardingPopup.style.display !== 'none') {
            onboardingPopup.querySelector('button').click();
            return true;
        }
        return false;
        """
    )


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
        type_onboarding_recovery_phrase(driver, recovery_phrase)

        button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[5]/button"

        button = driver.find_element(By.XPATH, button_xpath)
        button.click()

    wait.until(EC.url_contains("completion"))

    if "completion" in driver.current_url:
        try:
            button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[3]/button"
            click_element(driver, button_xpath)

            wait.until(EC.url_contains("pin-extension"))

            button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/button"
            click_element(driver, button_xpath)
            click_element(driver, button_xpath)

            wait.until(EC.url_contains("home"))
            wait.until(
                lambda driver: driver.execute_script(
                    "return document.readyState == 'complete'"
                )
            )

            close_home_onboarding_popup(driver)

            extension_id = get_extension_id(driver)
            extension_url = f"chrome-extension://{extension_id}/home.html"
            driver.get(extension_url)

        # ? added exception
        except Exception as e:
            print(e)


def import_an_existing_wallet(driver: webdriver.Chrome):
    button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/ul/li[3]/button"
    click_element(driver, button_xpath)


def import_private_key(driver: webdriver.Chrome, private_key: str) -> None:
    extension_id = get_extension_id(driver)
    extension_url = f"chrome-extension://{extension_id}/home.html"
    driver.get(extension_url)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.url_to_be(extension_url))

    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.url_to_be(extension_url))
        wait.until(
            lambda driver: driver.execute_script(
                "return document.readyState == 'complete'"
            )
        )

        print("opening accounts popup")
        xpath = "//*[@id='app-content']/div/div[2]/div/div[2]/button"
        parent_elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        parent_elem.click()

        # get the amount of accounts currently in the wallet
        account_list_popup_xpath = "/html/body/div[3]/div[3]/div/section"
        popup_elem = wait.until(
            EC.presence_of_element_located((By.XPATH, account_list_popup_xpath))
        )
        # try:
        #     search_input = popup_elem.find_element(
        #         By.CSS_SELECTOR, "input[type='search']"
        #     )
        #     print("Search input field found")
        # except Exception as e:
        #     print("Search input field not found:", e)

        # parent_elem = popup_elem.find_element(By.XPATH, "./div[1]")
        # print(parent_elem.text)
        # child_divs = parent_elem.find_elements(By.XPATH, "./div")
        # accounts_array = [child_div for child_div in child_divs]
        # accounts = len(accounts_array)
        # print("Accounts", accounts)

        print("select add account")
        last_div = popup_elem.find_elements(By.XPATH, "./div")[-1]
        last_div.find_element(By.XPATH, ".//button").click()

        print("select import account")
        xpath = "/html/body/div[3]/div[3]/div/section/div/div[2]/button"
        import_button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        import_button.click()

        print("paste private key")
        xpath = "//*[@id='private-key-box']"
        input_field = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        input_field.send_keys(private_key)

        print("select import")
        xpath = "/html/body/div[3]/div[3]/div/section/div/div/div[2]/button[2]"
        import_button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        import_button.click()

    except Exception as e:
        print(e)


def onboard(driver: webdriver.Chrome) -> None:
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

    password = getpass.getpass(ENTER_PASSWORD_TEXT)
    while len(password) < 8:
        print("Password must be at least 8 characters long")
        password = getpass.getpass(ENTER_PASSWORD_TEXT)

    click_element(driver, "//*[@id='onboarding__terms-checkbox']")

    create_a_new_wallet(driver, password)

    print("Onboarding complete")


def main():
    extension_dir = os.path.join(os.getcwd(), "extension")
    extension_path = os.path.join(extension_dir, f"{SupportedVersions.LATEST}.zip")

    if not os.path.exists(extension_path):
        print("Downloading MetaMask extension...")
        download_extension(SupportedVersions.LATEST, extension_dir)

    extension_path = os.path.abspath(f"extension/{SupportedVersions.LATEST}.zip")

    driver = setup_chrome_with_extension(extension_path)

    onboard(driver)

    import_private_key(driver, "your private key here")
    import_private_key(driver, "your private key here")
    import_private_key(driver, "your private key here")
    import_private_key(driver, "your private key here")
    import_private_key(driver, "your private key here")

    input("Press Enter to close the browser...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        quit()
