from urllib.parse import quote
from typing import Union

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from utils.constants.prompts import CONFIRM_PASSWORD_TEXT
from utils.constants.values import DEFAULT_TIMEOUT
from utils.enums.metamask_extension import SupportedVersion
from utils.inputs import get_password

from storage.extension import ExtensionStorage

from credentials import SecureCredentialStorage
from setup import run_script, setup_chrome_driver_for_metamask


def get_extension_home_url() -> str:
    storage = ExtensionStorage()

    extension_url = storage.get_extension_base_url("metamask")
    return extension_url + "/home.html"


def click_element(driver: webdriver, xpath: str):
    elem = driver.find_element(By.XPATH, xpath)
    if elem:
        elem.click()


# * SELENIUM HELPER FUNCTION
def get_open_tabs(driver: webdriver) -> list:
    return driver.window_handles


# * SELENIUM HELPER FUNTION
def close_tab(driver: webdriver, tab_index: int) -> None:
    driver.switch_to.window(driver.window_handles[tab_index])
    driver.close()


def create_a_new_wallet(driver: webdriver, password: str):
    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)

    button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/ul/li[2]/button"
    click_element(driver, button_xpath)

    wait.until(EC.url_contains("metametrics"))

    if "metametrics" in driver.current_url:
        button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/button[1]"
        click_element(driver, button_xpath)

    wait.until(EC.url_contains("create-password"))

    if "create-password" in driver.current_url:
        password_input_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/form/div[1]/label/input"
        input_elem = driver.find_element(By.XPATH, password_input_xpath)
        if input_elem:
            input_elem.send_keys(password)

        confirm_password_input_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[2]/form/div[2]/label/input"
        input_elem = driver.find_element(By.XPATH, confirm_password_input_xpath)
        if input_elem:
            input_elem.send_keys(password)

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
        import pyperclip

        xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[6]/button"
        click_element(driver, xpath)

        xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[6]/div/div/a[2]"
        click_element(driver, xpath)

        if not pyperclip.is_available():
            print("Copy functionality unavailable!")

        recovery_phrase = pyperclip.paste()
        print(f"Recovery Phrase: {recovery_phrase}")

        # TODO Save the recovery phrase somewhere safe
        xpath = "//*[@id='app-content']/div/div[2]/div/div/div/div[6]/div/button"
        click_element(driver, xpath)

    wait.until(EC.url_contains("confirm-recovery-phrase"))

    if "confirm-recovery-phrase" in driver.current_url:
        recovery_words = recovery_phrase.split()
        run_script(
            driver, "input-recovery-phrase.js", args={"recovery_words": recovery_words}
        )

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

            run_script(driver, "button-tooltip-close.js")

            extension_url = get_extension_home_url()
            driver.get(extension_url)

        # ? added exception
        except Exception as e:
            print(e)


def import_an_existing_wallet(driver: webdriver):
    button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/ul/li[3]/button"
    click_element(driver, button_xpath)


def open_multichain_account_picker(driver: webdriver) -> WebElement:
    extension_url = get_extension_home_url()
    driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))

    xpath = "//*[@id='app-content']/div/div[2]/div/div[2]/button"
    account_picker_button = wait.until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )
    account_picker_button.click()

    popup_elem = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section[role='dialog']"))
    )

    return popup_elem


def close_dialog(locator: WebElement):
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    close_button = wait.until(
        EC.presence_of_element_located((By.XPATH, ".//header//button"))
    )
    close_button.click()


def get_multichain_account_length(locator: WebElement) -> int:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    list_wrapper_class_name = "multichain-account-menu-popover__list"
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, list_wrapper_class_name)))

    list_item_class_name = "multichain-account-list-item"
    account_list_items = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, list_item_class_name))
    )

    return len(account_list_items)


def get_multichain_account_index(locator: WebElement, account_address: str) -> int:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    list_wrapper_class_name = "multichain-account-menu-popover__list"
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, list_wrapper_class_name)))

    list_item_class_name = "multichain-account-list-item"
    account_list_items = wait.until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, list_item_class_name))
    )

    for index, account in enumerate(account_list_items):
        wait = WebDriverWait(account, timeout=DEFAULT_TIMEOUT)
        account_address_elem = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, ".//p[@data-testid='account-list-address']")
            )
        )
        if (
            account_address_elem.text[:7] == account_address[:7]
            and account_address_elem.text[-5:] == account_address[-5:]
        ):
            return index

    return -1


def get_multichain_accounts_list(locator: WebElement) -> list[WebElement]:
    list_wrapper_class_name = "multichain-account-menu-popover__list"
    list_wrapper = locator.find_element(By.CLASS_NAME, list_wrapper_class_name)

    list_item_class_name = "multichain-account-list-item"
    account_list_items = list_wrapper.find_elements(By.CLASS_NAME, list_item_class_name)
    accounts_array = [multichain_account for multichain_account in account_list_items]

    return accounts_array


def switch_account(locator: WebElement, account_address: str) -> bool:
    index = get_multichain_account_index(locator, account_address)

    if index == -1:
        return False

    accounts = get_multichain_accounts_list(locator)

    if len(accounts) < index:
        return False

    accounts[index].click()

    return True


def import_account(driver: webdriver, private_key: str) -> str:
    from web3 import Web3

    account = Web3().eth.account.from_key(private_key)
    ethereum_address = account.address

    extension_url = get_extension_home_url()
    driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))

    try:
        wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
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

        popup_elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section[role='dialog']"))
        )

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

        return ethereum_address

    except Exception as e:
        print(e)


def onboard_extension(driver: webdriver) -> webdriver:
    extension_url = get_extension_home_url()
    original_window = driver.current_window_handle
    open_window_handles = driver.window_handles

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(
        lambda driver: len(driver.window_handles) > len(open_window_handles)
    )  # ? wait for the extension to open in a new tab

    open_window_handles = driver.window_handles
    onboarding_window = None

    for window_handle in driver.window_handles:
        driver.switch_to.window(window_handle)

        if "offscreen.html" in driver.current_url:  # ? offscreen tab
            driver.close()
            driver.switch_to.window(original_window)
            wait.until(
                lambda driver: len(driver.window_handles)
                == len(open_window_handles) - 1
            )

        if "#onboarding" in driver.current_url:  # ? onboarding tab
            onboarding_window = window_handle

    driver.switch_to.window(onboarding_window)  # ? switch to the onboarding tab
    driver.get(extension_url)

    wait.until(EC.url_contains(extension_url + "#onboarding"))
    wait.until(lambda driver: run_script(driver, "readyState.js"))

    print("Starting MetaMask onboarding...")

    storage = SecureCredentialStorage()
    password = get_password(CONFIRM_PASSWORD_TEXT)
    verified = storage.verify_credential("metamask", "password_hash", password)

    if verified:
        terms_checkbox_xpath = "//*[@id='onboarding__terms-checkbox']"
        terms_checkbox = driver.find_element(By.XPATH, terms_checkbox_xpath)

        if not terms_checkbox.is_selected():
            terms_checkbox.click()

        create_a_new_wallet(driver, password)

        print("Onboarding complete")
        return driver
    else:
        raise Exception("Failed to verify password")


def add_custom_network(driver: webdriver, network: dict) -> None:
    extension_url = get_extension_home_url()
    driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))

    xpath = "//*[@id='app-content']/div/div[2]/div/div[1]/button"
    trigger_button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    trigger_button.click()

    popup_dialog = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section[role='dialog']"))
    )

    print("select add custom network")
    last_div = popup_dialog.find_elements(By.XPATH, "./div")[-1]
    last_div.find_element(By.XPATH, ".//button").click()

    try:
        run_script(driver, "input-network-details.js", args={"network": network})
    except Exception as e:
        print(e)

    # add RPC url
    trigger_button = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "/html/body/div[3]/div[3]/div/section/div/div[1]/div[2]/div/button",
            )
        )
    )
    trigger_button.click()

    add_rpc_button = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "/html/body/div[3]/div[3]/div/section/div/div[1]/div[2]/div[2]/div/div/button",
            )
        )
    )
    add_rpc_button.click()

    rpc_url_input = wait.until(EC.presence_of_element_located((By.ID, "rpcUrl")))

    rpc_url_input.send_keys(network["rpc_url"])

    complete_action_button = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "/html/body/div[3]/div[3]/div/section/div/div[2]/button",
            )
        )
    )
    complete_action_button.click()

    if network["block_explorer_url"]:
        trigger_xpath = (
            "/html/body/div[3]/div[3]/div/section/div/div[1]/div[5]/div[1]/button"
        )
        trigger_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    trigger_xpath,
                )
            )
        )
        trigger_button.click()

        add_block_explorer_xpath = "/html/body/div[3]/div[3]/div/section/div/div[1]/div[5]/div[2]/div/div/button"
        add_block_explorer_url = wait.until(
            EC.presence_of_element_located((By.XPATH, add_block_explorer_xpath))
        )
        add_block_explorer_url.click()

        block_explorer_input = wait.until(
            EC.presence_of_element_located((By.ID, "additional-rpc-url"))
        )

        block_explorer_input.send_keys(network["block_explorer_url"])

        complete_action_button = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[3]/div[3]/div/section/div/div[2]/button",
                )
            )
        )
        complete_action_button.click()

    save_xpath = "/html/body/div[3]/div[3]/div/section/div/div[2]/button"
    save_button = wait.until(EC.presence_of_element_located((By.XPATH, save_xpath)))
    save_button.click()


def switch_to_network(driver: webdriver, network_name: str) -> None:
    extension_url = get_extension_home_url()
    driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))

    xpath = "//*[@id='app-content']/div/div[2]/div/div[1]/button"
    trigger_button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    trigger_button.click()

    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section[role='dialog']"))
    )

    print("select a network")
    network_list_xpath = "/html/body/div[3]/div[3]/div/section/div[1]/div[3]/div[2]"
    network_list_wrapper = wait.until(
        EC.presence_of_element_located((By.XPATH, network_list_xpath))
    )
    network_list = network_list_wrapper.find_elements(By.XPATH, ".//p")
    for network in network_list:
        if network.text == network_name:
            network.click()
            break
        print(network.text)


def disconnect_dapp_permission(driver: webdriver, site_url: str):
    review_permissions_url = (
        get_extension_home_url() + "#review-permissions/" + quote(site_url, safe="")
    )
    driver.get(review_permissions_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(review_permissions_url))

    is_connected = False

    try:
        wait = WebDriverWait(driver, timeout=10)
        content_class_name = "multichain-connection-list-item"
        wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, content_class_name))
        )
        is_connected = True
    except Exception:
        wait = WebDriverWait(driver, timeout=10)
        content_class_name = "connections-page__no-site-connected-content"
        no_site_connected_content = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, content_class_name))
        )
        print(no_site_connected_content.text)

    if is_connected:
        disconnect_btn_xpath = (
            "//*[@id='app-content']/div/div/div/div/div[3]/div/button"
        )
        disconnect_button = wait.until(
            EC.presence_of_element_located((By.XPATH, disconnect_btn_xpath))
        )
        disconnect_button.click()

        popup_elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section[role='dialog']"))
        )

        wait = WebDriverWait(popup_elem, timeout=DEFAULT_TIMEOUT)

        last_div = wait.until(EC.presence_of_all_elements_located((By.XPATH, "./div")))[
            -1
        ]

        wait = WebDriverWait(last_div, timeout=DEFAULT_TIMEOUT)

        disconnect_all_button = wait.until(
            EC.presence_of_element_located((By.XPATH, ".//button"))
        )
        disconnect_all_button.click()

        print("Disconnected from", site_url)


def main():
    options = Options()
    service = Service()

    driver = setup_chrome_driver_for_metamask(
        options=options,
        service=service,
        metamask_version=SupportedVersion.LATEST,
        headless=False,
    )

    onboard_extension(driver)

    zetachain_network = {
        "name": "ZetaChain Mainnet",
        "rpc_url": "https://zetachain-mainnet.public.blastapi.io/",
        "chain_id": 7000,
        "currency_symbol": "ZETA",
        "block_explorer_url": "https://explorer.zetachain.com",
    }

    add_custom_network(driver, zetachain_network)
    switch_to_network(driver, zetachain_network["name"])

    input("Press Enter to close the browser...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        quit()
