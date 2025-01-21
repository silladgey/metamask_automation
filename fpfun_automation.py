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


FINGERPUMP_BASE_URL = "https://www.fingerpump.fun"


def account_connect(locator: WebElement) -> WebElement:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    try:
        connect_trigger = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@data-test='connect-wallet-button']",
                )
            )
        )

        is_ready = wait.until(
            lambda driver: connect_trigger.get_attribute("data-is-loading") == "false"
        )

        if is_ready:
            return connect_trigger
    except Exception:
        return None


def account_disconnect(locator: WebElement) -> WebElement:
    wait = WebDriverWait(locator, timeout=DEFAULT_TIMEOUT)

    try:
        disconnect_trigger = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='root']/div/div/div/div[2]/div/div/button",
                )
            )
        )

        if disconnect_trigger:
            return disconnect_trigger
    except Exception:
        return None


def is_account_connected(locator: WebElement) -> bool:
    wait = WebDriverWait(locator, timeout=10)

    try:
        trigger = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//*[@id='root']/div/div/div/div[2]/div/div/button",
                )
            )
        )

        if trigger.get_attribute("data-test") == "connect-wallet-button":
            return False
        else:
            return True
    except Exception:
        return False


def open_fingerpump_game(driver: webdriver) -> WebElement:
    window_handles = driver.window_handles

    try:
        driver.switch_to.new_window("tab")
        driver.get(FINGERPUMP_BASE_URL + "/game")

        wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
        wait.until(lambda driver: len(driver.window_handles) == len(window_handles) + 1)
        wait.until(EC.url_to_be(FINGERPUMP_BASE_URL + "/game"))

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
        picker = open_dialog(locator, connect_account_trigger)
        return picker
    except Exception:
        return None


def connect_game_to_metamask(driver: webdriver):
    page_body = open_fingerpump_game(driver)
    wallet_picker = open_wallet_picker(page_body)

    if not wallet_picker:
        return

    wait = WebDriverWait(wallet_picker, timeout=DEFAULT_TIMEOUT)

    wallets_list_items = wait.until(
        EC.presence_of_all_elements_located(
            (By.XPATH, "//*[@id='radix-:r0:']/div[1]/div/div/div/div[2]/ul//span")
        )
    )

    wallet_trigger = None

    for item in wallets_list_items:
        if item.text == "MetaMask":
            wallet_trigger = item

    is_connection_successful = False

    if wallet_trigger:
        is_connection_successful = connect_account_to_dapp(driver, wallet_trigger)

        if is_connection_successful:
            status = is_account_connected(page_body)
            print("Connected to wallet:", status)

    while not is_connection_successful:
        wait = WebDriverWait(driver, timeout=10)
        try:
            trigger = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@id='radix-:r0:']/div[1]/div/div/div/div[2]/div[2]/div[2]/button",
                    )
                )
            )
            is_connection_successful = connect_account_to_dapp(driver, trigger)

            status = is_account_connected(page_body)
            print("Connected to wallet:", status)
            wait.until(EC.url_to_be(FINGERPUMP_BASE_URL + "/game"))
        except Exception:
            close_dialog(wallet_picker)
            wait.until(EC.url_to_be(FINGERPUMP_BASE_URL + "/game"))
            connect_game_to_metamask(driver)


def play_game(driver: webdriver):
    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)

    play_xpath = "//*[@id='root']/div/main/div[1]/div/button"
    play_button = wait.until(EC.presence_of_element_located((By.XPATH, play_xpath)))
    try:
        play_button.click()
    except Exception as e:
        print(e)

    wait.until(lambda driver: len(driver.window_handles) > 3)
    new_tab = driver.window_handles[-1]
    driver.switch_to.window(new_tab)

    print("Current tab title:", driver.title)

    try:
        import time

        time.sleep(2)
        wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )

        connect_script = """
        const button = document.querySelector("button[data-testid='confirm-footer-button']");
        if (button) {
            button.click();
        }
        """

        driver.execute_script(connect_script)

        driver.switch_to.window(driver.window_handles[2])

    except Exception as e:
        print(e)

    import requests

    js_url = "https://raw.githubusercontent.com/silladgey/fp-fun-typing/refs/heads/automation/automate.js"
    response = requests.get(js_url, timeout=10)

    if response.status_code == 200:
        js_code = response.text
        import time

        time.sleep(2)
        driver.execute_script(js_code)
        wait.until(
            lambda driver: driver.execute_script(
                "return document.readyState == 'complete'"
            )
        )
    else:
        print(f"Failed to load JavaScript code. Status code: {response.status_code}")


def mint_fingerpuppet(driver: webdriver):
    # TODO Check that the account has enough funds to mint
    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    xpath = "//*[@id='dailyNfts']/div/div/div/div/div[2]/div/button"
    mint_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    mint_button.click()

    # TODO Approve transaction: confirmation-submit-button
    wait.until(lambda driver: len(driver.window_handles) > 3)
    new_tab = driver.window_handles[-1]
    driver.switch_to.window(new_tab)

    notification_page = "notification.html"
    wait.until(EC.url_contains(notification_page))

    print("Current tab:", driver.current_url)

    import time

    time.sleep(2)

    wait.until(lambda driver: run_script(driver, "readyState.js"))

    # wrapper = wait.until(
    #     EC.presence_of_element_located((By.CLASS_NAME, "confirmation-page"))
    # )

    # print("wrapper")

    # wait = WebDriverWait(wrapper, timeout=DEFAULT_TIMEOUT)
    # title = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h3")))

    # print("Title:", title.text)

    connect_script = """
    const button = document.querySelector("button[data-testid='confirm-footer-button']");
    if (button) {
        button.click();
    }
    """

    driver.execute_script(connect_script)

    driver.switch_to.window(driver.window_handles[2])

    # Print out the currently open tabs
    all_tabs = driver.window_handles
    for tab in all_tabs:
        if "fingerpump.fun" not in driver.current_url:
            driver.switch_to.window(tab)
            print(driver.current_url)

    confirmation_xpath = "//*[@id='dailyNfts']/div/div/div/div[2]"
    confirmation_popup = wait.until(
        EC.presence_of_element_located((By.XPATH, confirmation_xpath))
    )

    if confirmation_popup.is_displayed():
        print(confirmation_popup.text)
        nft_img_xpath = "//*[@id='dailyNfts']/div/div/div/div[2]/div/div/div[1]/img"

        nft_img = wait.until(EC.presence_of_element_located((By.XPATH, nft_img_xpath)))

        if nft_img.is_displayed():
            print("NFT minted successfully!")

    wait.until(lambda driver: len(driver.window_handles) <= 3)
    driver.switch_to.window(driver.window_handles[2])


def mint_hand_model_nft(driver: webdriver):
    # TODO: mint nft button: //*[@id='root']/div/main/div[2]/div/div/div/div/div[1]/div/div[2]/button[2]
    driver.get("https://www.fingerpump.fun/dashboard")


def disconnect_account(driver: webdriver):
    driver.switch_to.window(driver.window_handles[2])

    game_url = "https://www.fingerpump.fun/game"

    if driver.current_url != game_url:
        driver.get(game_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(game_url))

    try:
        disconnect_button = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='root']/div/div/div/div[2]/div/div/button")
            )
        )

        disconnect_button.click()

    except Exception as e:
        print(e)

    driver.close()
    driver.switch_to.window(driver.window_handles[1])

    disconnect_dapp_permission(driver, "https://www.fingerpump.fun")


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

    zetachain_network = {
        "name": "ZetaChain Mainnet",
        "rpc_url": "https://zetachain-mainnet.public.blastapi.io/",
        "chain_id": 7000,
        "currency_symbol": "ZETA",
        "block_explorer_url": "https://explorer.zetachain.com",
    }

    add_custom_network(driver, zetachain_network)

    network = switch_to_network(driver, zetachain_network["name"])

    if network is None:
        driver.quit()

    print(f"Connected to network {network}")

    for address in addresses:
        account_picker = open_multichain_account_picker(driver)
        eth_address = switch_account(account_picker, address)
        print(f"Switched to account {eth_address}")

        connect_game_to_metamask(driver)
        play_game(driver)
        mint_fingerpuppet(driver)
        disconnect_account(driver)

    driver.quit()
