from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement

from extension.helpers import open_dialog, close_dialog, run_script

from metamask_automation import (
    add_custom_network,
    connect_account_to_dapp,
    disconnect_dapp_permission,
    import_multichain_account,
    onboard_extension,
    open_multichain_account_picker,
    setup_chrome_driver_for_metamask,
    switch_account,
    switch_to_network,
)

from utils.constants.values import DEFAULT_TIMEOUT
from utils.enums.metamask_extension import SupportedVersion

EARN_TAKER_BASE_URL = "https://earn.taker.xyz/"

def account_connect(locator: WebElement) -> WebElement:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    try:
        connect_trigger = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='headlessui-popover-button-:r1:']",
                )
            )
        )

        is_ready = connect_trigger.text == "Connect Wallet"
        print("is_ready", is_ready)

        if is_ready:
            return connect_trigger
    except Exception:
        return None

def is_account_connected(locator: WebElement) -> bool:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    try:
        trigger = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='headlessui-popover-button-:r1:']",
                )
            )
        )
        
        wait.until(
            lambda driver: trigger.text != "Connecting..."
        )
        
        is_connected = "Connect Wallet" not in trigger.text

        if is_connected:
            return True
        return False
    except Exception:
        return False

def open_taker_earn(driver: webdriver) -> WebElement:
    window_handles = driver.window_handles

    try:
        driver.switch_to.new_window("tab")
        driver.get(EARN_TAKER_BASE_URL)

        wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
        wait.until(lambda driver: len(driver.window_handles) == len(window_handles) + 1)
        wait.until(EC.url_to_be(EARN_TAKER_BASE_URL))

        page_body = wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return page_body

    except Exception:
        return None


def open_wallet_picker(locator: WebElement) -> WebElement:
    if is_account_connected(locator):
        return None

    connect_account_trigger = account_connect(locator)

    if not connect_account_trigger:
        return None

    try:
        connect_account_trigger.click()
    except Exception:
        return None
    
    
def connect_site_to_metamask(driver: webdriver):
    page_body = open_taker_earn(driver)
    open_wallet_picker(driver)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)

    wallet_trigger = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[@id='headlessui-popover-panel-:r3:']/div/div/div[2]")
        )
    )

    is_connection_successful = False

    if wallet_trigger:
        is_connection_successful = connect_account_to_dapp(driver, wallet_trigger)

        if is_connection_successful:
            status = is_account_connected(page_body)
            print("Connected to wallet:", status)

    count = 0
    while not is_connection_successful:
        wait = WebDriverWait(driver, timeout=10)
        try:
            open_wallet_picker(driver)
            trigger = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[@id='headlessui-popover-panel-:r{count + 4}:']/div/div/div[2]")
                )
            )
            is_connection_successful = connect_account_to_dapp(driver, trigger)

            status = is_account_connected(page_body)
            print("Connected to wallet:", status)
            count += 1
            wait.until(EC.url_to_be(EARN_TAKER_BASE_URL))
        except Exception:
            wait.until(EC.url_to_be(EARN_TAKER_BASE_URL))
            connect_site_to_metamask(driver)

if __name__ == "__main__":
    options = Options()
    service = Service()

    driver = setup_chrome_driver_for_metamask(
        options=options,
        service=service,
        metamask_version=SupportedVersion.LATEST,
        headless=False,
    )

    onboard_extension(driver)
    
    private_keys = []  # * Add private keys here
    addresses = []

    for private_key in private_keys:
        address = import_multichain_account(driver, private_key)
        print(f"Importing address {address}...")
        addresses.append(address)

    print(f"Imported {len(addresses)} addresses")
    
    taker_network = {
        "name": "Taker Mainnet",
        "rpc_url": "https:/rpc-mainnet.taker.xyz/",
        "chain_id": 1125,
        "currency_symbol": "TAKER",
        "block_explorer_url": "https://explorer.taker.xyz",
    }

    add_custom_network(driver, taker_network)

    network = switch_to_network(driver, taker_network["name"])
    
    if network is None:
        driver.quit()
        
    print(f"Connected to network {network}")

    for address in addresses:
        connect_site_to_metamask(driver)
        input()
    
    driver.quit()
