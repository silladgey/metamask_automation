from urllib.parse import quote
from web3 import Web3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from extension.helpers import get_extension_home_url, open_dialog, run_script
from extension.onboarding import onboard_extension
from extension.setup import setup_chrome_driver_for_metamask

from storage.extension import ExtensionStorage

from utils.constants.values import DEFAULT_TIMEOUT
from utils.enums.metamask_extension import SupportedVersion


def import_multichain_account(driver: webdriver, private_key: str) -> str:
    # ! TODO validate private key
    account = Web3().eth.account.from_key(private_key)
    eth_address = account.address

    def add_account(locator: WebElement):
        wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

        # ? Click "Add account or hardware wallet"
        action_button_xpath = (
            "//*[@data-testid='multichain-account-menu-popover-action-button']"
        )

        wait.until(
            EC.presence_of_element_located((By.XPATH, action_button_xpath))
        ).click()

        # ? Select "Import account"
        add_imported_account_button_xpath = (
            "//*[@data-testid='multichain-account-menu-popover-add-imported-account']"
        )

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, add_imported_account_button_xpath)
            )
        ).click()

        # ? Enter private key string
        input_field_xpath = "//*[@id='private-key-box']"
        input_field = wait.until(
            EC.presence_of_element_located((By.XPATH, input_field_xpath))
        )
        input_field.send_keys(private_key)

        # ? Click "Import"
        import_account_confirm_xpath = (
            "//*[@data-testid='import-account-confirm-button']"
        )

        wait.until(
            EC.presence_of_element_located((By.XPATH, import_account_confirm_xpath))
        ).click()

    account_picker = open_multichain_account_picker(driver)
    add_account(account_picker)

    return eth_address


def open_multichain_account_picker(driver: webdriver) -> WebElement:
    extension_url = get_extension_home_url()

    if driver.current_url != extension_url:
        driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))

    account_menu_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[@data-testid='account-menu-icon']")
        )
    )

    picker = open_dialog(driver, account_menu_button)
    return picker


def get_multichain_account_list(locator: WebElement) -> list[WebElement]:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    list_wrapper = wait.until(
        EC.presence_of_element_located(
            (By.CLASS_NAME, "multichain-account-menu-popover__list")
        )
    )

    wait = WebDriverWait(list_wrapper, timeout=DEFAULT_TIMEOUT)

    account_list_items = wait.until(
        EC.presence_of_all_elements_located(
            (By.CLASS_NAME, "multichain-account-list-item")
        )
    )

    return account_list_items


def get_multichain_account_index(locator: WebElement, account_address: str) -> int:
    account_list_items = get_multichain_account_list(locator)

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


def get_multichain_account_length(locator: WebElement) -> list[WebElement]:
    multichain_accounts = get_multichain_account_list(locator)
    return len(multichain_accounts)


def switch_account(locator: WebElement, account_address: str) -> bool:
    index = get_multichain_account_index(locator, account_address)

    if index == -1:
        return False

    accounts = get_multichain_account_list(locator)

    if len(accounts) < index:
        return False

    accounts[index].click()

    return True


def add_custom_network(driver: webdriver, network: dict) -> None:
    def add_network_details(locator: WebElement):
        wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

        add_custom_network_xpath = "/html/body/div[3]/div[3]/div/section/div[2]/button"
        wait.until(
            EC.presence_of_element_located((By.XPATH, add_custom_network_xpath))
        ).click()

        # ? Network name
        network_name_input = wait.until(
            EC.presence_of_element_located((By.ID, "networkName"))
        )
        network_name_input.send_keys(network["name"])

        # ? Default RPC URL
        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@data-testid='test-add-rpc-drop-down']")
            )
        ).click()  # ? Click trigger

        wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[3]/div[3]/div/section/div/div[1]/div[2]/div[2]/div/div/button",
                )
            )
        ).click()  # ? Click "Add Custom RPC"

        rpc_url_input = wait.until(EC.presence_of_element_located((By.ID, "rpcUrl")))
        rpc_url_input.send_keys(network["rpc_url"])  # ? Enter RPC URL

        wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[3]/div[3]/div/section/div/div[2]/button",
                )
            )
        ).click()  # ? Click "Save"

        # ? Chain ID
        chain_id_input = wait.until(EC.presence_of_element_located((By.ID, "chainId")))
        chain_id_input.send_keys(network["chain_id"])

        # ? Currency symbol
        currency_symbol_input = wait.until(
            EC.presence_of_element_located((By.ID, "nativeCurrency"))
        )
        currency_symbol_input.send_keys(network["currency_symbol"])

        # ? Block Explorer URL
        if "block_explorer_url" in network and network["block_explorer_url"]:
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//*[@data-testid='test-explorer-drop-down']",
                        )
                    )
                ).click()  # ? Click trigger
            except Exception as e:
                print(e)

            wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[3]/div[3]/div/section/div/div[1]/div[5]/div[2]/div/div/button",
                    )
                )
            ).click()  # ? Click "Add a block explorer URL"

            block_explorer_url_input = wait.until(
                EC.presence_of_element_located((By.ID, "additional-rpc-url"))
            )
            block_explorer_url_input.send_keys(
                network["block_explorer_url"]
            )  # ? Enter block explorer URL

            wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[3]/div[3]/div/section/div/div[2]/button",
                    )
                )
            ).click()  # ? Click "Add URL"

        wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[3]/div[3]/div/section/div/div[2]/button")
            )
        ).click()  # ? Click "Save"

    network_picker = open_network_picker(driver)
    add_network_details(network_picker)


def open_network_picker(driver: webdriver) -> WebElement:
    extension_url = get_extension_home_url()

    if driver.current_url != extension_url:
        driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))

    network_display_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[@data-testid='network-display']")
        )
    )

    picker = open_dialog(driver, network_display_button)
    return picker


def switch_to_network(driver: webdriver, network_name: str) -> None:
    extension_url = get_extension_home_url()

    if driver.current_url != extension_url:
        driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))

    network_picker = open_network_picker(driver)

    wait = WebDriverWait(network_picker, timeout=DEFAULT_TIMEOUT)

    # ? Network selection
    network_list = wait.until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "/html/body/div[3]/div[3]/div/section/div[1]/div[3]/div[2]//p")
        )
    )

    network_to_select = None

    for network in network_list:
        if network.text == network_name:
            network_to_select = network

    if network_to_select:
        network_to_select.click()


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
