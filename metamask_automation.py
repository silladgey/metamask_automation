from urllib.parse import quote
from web3 import Web3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from extension.helpers import (
    get_metamask_extension_url,
    get_metamask_home_url,
    open_dialog,
    close_dialog,
)
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
    home_url = get_metamask_home_url()

    if driver.current_url != home_url:
        driver.get(home_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(home_url))

    account_menu_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[@data-testid='account-menu-icon']")
        )
    )

    picker = open_dialog(driver, account_menu_button)
    return picker


def list_multichain_account_items(locator: WebElement) -> list[WebElement]:
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
    account_list_items = list_multichain_account_items(locator)

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
    multichain_accounts = list_multichain_account_items(locator)
    return len(multichain_accounts)


def switch_account(locator: WebElement, account_address: str) -> str:
    accounts = list_multichain_account_items(locator)
    index = get_multichain_account_index(locator, account_address)

    # ? Account list is empty
    if len(accounts) < index:
        return None

    # ? Account not found
    if index == -1:
        return None

    accounts[index].click()

    return account_address


def add_custom_network(driver: webdriver, network: dict) -> bool:
    def click_save(wrapper_locator: WebElement) -> bool:
        wait = WebDriverWait(wrapper_locator, timeout=DEFAULT_TIMEOUT)
        try:
            wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "/html/body/div[3]/div[3]/div/section/div/div[2]/button",
                    )
                )
            ).click()
            return True
        except Exception:
            return False

    def add_network_details(locator: WebElement) -> bool:
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

        click_save(locator)

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
            except Exception:
                return click_save(locator)

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

            click_save(locator)

        return click_save(locator)

    network_picker = open_network_picker(driver)

    try:
        add_network_details(network_picker)

        wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)

        success_notification = wait.until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "actionable-message--success")
            )
        )

        if success_notification:
            print(success_notification.text)
            return True

    except Exception:
        close_dialog(network_picker)
        close_dialog(network_picker)

    return False


def open_network_picker(driver: webdriver) -> WebElement:
    home_url = get_metamask_home_url()

    if driver.current_url != home_url:
        driver.get(home_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(home_url))

    network_display_button = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[@data-testid='network-display']")
        )
    )

    picker = open_dialog(driver, network_display_button)
    return picker


def list_network_items(locator: WebElement) -> list[WebElement]:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    network_list_items = wait.until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "/html/body/div[3]/div[3]/div/section/div[1]/div[3]/div[2]//p")
        )
    )

    return network_list_items


def current_network_status(locator: WebElement) -> str:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    connected_network_wrapper = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[@data-testid='network-display']")
        )
    )

    wait = WebDriverWait(connected_network_wrapper, timeout=DEFAULT_TIMEOUT)

    connected_network = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, ".//span[contains(@class, 'mm-text')]")
        )
    ).text

    return connected_network


def switch_to_network(driver: webdriver, network_name: str) -> str:
    home_url = get_metamask_home_url()

    if driver.current_url != home_url:
        driver.get(home_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(home_url))

    network_picker = open_network_picker(driver)
    network_list_items = list_network_items(network_picker)

    network_to_select = None

    for network_item in network_list_items:
        if network_item.text == network_name:
            network_to_select = network_item

    if not network_to_select:
        print("Network not found")
        close_dialog(network_picker)
        return current_network_status(driver)

    network_to_select.click()

    return current_network_status(driver)


def connect_account_to_dapp(driver: webdriver, connect_trigger: WebElement) -> bool:
    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)

    original_tab = driver.current_window_handle
    window_handles = driver.window_handles

    if not connect_trigger:
        return False

    connect_trigger.click()

    wait.until(lambda driver: len(driver.window_handles) == len(window_handles) + 1)

    metamask_notification_tab = driver.window_handles[-1]
    driver.switch_to.window(metamask_notification_tab)

    extension_url = get_metamask_extension_url()
    wait.until(EC.url_contains(extension_url + "/notification.html"))

    try:
        driver.implicitly_wait(DEFAULT_TIMEOUT)

        for _ in range(500):
            try:
                if driver.find_element(By.CLASS_NAME, "permissions-connect"):

                    connect_page = driver.find_element(
                        By.XPATH, "//*[@data-testid='connect-page']"
                    )

                    action_prompt = connect_page.find_element(By.TAG_NAME, "h2")
                    print(action_prompt.text)

                    metamask_connect_script = """
                        const button = document.querySelector("button[data-testid='confirm-btn']");
                        if (button) {
                            button.click();
                        }
                        """

                    driver.execute_script(metamask_connect_script)

                    return True
            except Exception:
                pass
            driver.implicitly_wait(DEFAULT_TIMEOUT)

        driver.close()
        return False
    except Exception:
        driver.close()
        return False
    finally:
        driver.switch_to.window(original_tab)
        wait.until(lambda driver: len(driver.window_handles) == len(window_handles))


def disconnect_dapp_permission(driver: webdriver, site_url: str):
    home_url = get_metamask_home_url()

    site_url = quote(site_url, safe="")
    review_permissions_url = f"{home_url}#review-permissions/{site_url}"

    if driver.current_url != review_permissions_url:
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


if __name__ == "__main__":
    options = Options()
    service = Service()

    driver = setup_chrome_driver_for_metamask(
        options=options,
        service=service,
        metamask_version=SupportedVersion.LATEST,
        headless=False,
    )

    try:
        onboard_extension(driver)

        private_keys = []  # * Add private keys here
        addresses = []

        for private_key in private_keys:
            address = import_multichain_account(driver, private_key)
            print(f"Importing address {address}...")
            addresses.append(address)

        print(f"Imported {len(addresses)} addresses")

        network = current_network_status(driver)
        print("Connected to network", network)

        if network is None:
            driver.quit()

        # ! Implement your logic here

        driver.quit()
    except KeyboardInterrupt:
        driver.quit()
        quit()
