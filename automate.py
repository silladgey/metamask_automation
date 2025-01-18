from urllib.parse import quote

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


def onboarding_create_wallet(driver: webdriver, password: str):
    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)

    recovery_phrase_confirm_xpath = "//*[@data-testid='onboarding-create-wallet']"
    create_wallet_button = wait.until(
        EC.presence_of_element_located((By.XPATH, recovery_phrase_confirm_xpath))
    )

    if create_wallet_button.is_enabled():
        create_wallet_button.click()

    # ? Metametrics section
    wait.until(EC.url_contains("metametrics"))

    if "metametrics" in driver.current_url:
        recovery_phrase_confirm_xpath = "//*[@data-testid='metametrics-no-thanks']"
        wait.until(
            EC.presence_of_element_located((By.XPATH, recovery_phrase_confirm_xpath))
        ).click()

    # ? Create wallet password section
    wait.until(EC.url_contains("create-password"))

    if "create-password" in driver.current_url:
        create_password_xpath = "//*[@data-testid='create-password-new']"
        create_password_confirm_input = wait.until(
            EC.presence_of_element_located((By.XPATH, create_password_xpath))
        )

        if create_password_confirm_input.is_enabled():
            create_password_confirm_input.clear()
            create_password_confirm_input.send_keys(password)

        create_password_confirm_xpath = "//*[@data-testid='create-password-confirm']"
        create_password_confirm_input = wait.until(
            EC.presence_of_element_located((By.XPATH, create_password_confirm_xpath))
        )

        if create_password_confirm_input.is_enabled():
            create_password_confirm_input.clear()
            create_password_confirm_input.send_keys(password)

        recovery_phrase_confirm_xpath = "//*[@data-testid='create-password-terms']"
        create_password_terms_button = wait.until(
            EC.presence_of_element_located((By.XPATH, recovery_phrase_confirm_xpath))
        )

        if not create_password_terms_button.is_selected():
            create_password_terms_button.click()

        create_password_wallet_xpath = "//*[@data-testid='create-password-wallet']"
        create_password_wallet_button = wait.until(
            EC.presence_of_element_located((By.XPATH, create_password_wallet_xpath))
        )

        if create_password_wallet_button.is_enabled():
            create_password_wallet_button.click()

    # ? Secure wallet with secret recovery phrase section
    wait.until(EC.url_contains("secure-your-wallet"))

    if "secure-your-wallet" in driver.current_url:
        secure_wallet_xpath = (
            "//*[@data-testid='secure-wallet-recommended']"  # ? yes by default
        )

        wait.until(
            EC.presence_of_element_located((By.XPATH, secure_wallet_xpath))
        ).click()

    # ? Review secret recovery phrase section
    wait.until(EC.url_contains("review-recovery-phrase"))

    if "review-recovery-phrase" in driver.current_url:
        import pyperclip

        recovery_phrase_reveal_xpath = "//*[@data-testid='recovery-phrase-reveal']"
        wait.until(
            EC.presence_of_element_located((By.XPATH, recovery_phrase_reveal_xpath))
        ).click()

        copy_and_hide_xpath = (
            "//*[@id='app-content']/div/div[2]/div/div/div/div[6]/div/div/a[2]"
        )
        wait.until(
            EC.presence_of_element_located((By.XPATH, copy_and_hide_xpath))
        ).click()

        recovery_phrase = pyperclip.paste()  # ? get the recovery phrase from clipboard
        print(f"Recovery Phrase: {recovery_phrase}")
        print("Make sure to back it up!")

        # ! TODO Save the recovery phrase somewhere safe

        next_button_xpath = "//*[@data-testid='recovery-phrase-next']"
        wait.until(
            EC.presence_of_element_located((By.XPATH, next_button_xpath))
        ).click()

    # ? Confirm secret recovery phrase section
    wait.until(EC.url_contains("confirm-recovery-phrase"))

    if "confirm-recovery-phrase" in driver.current_url:
        recovery_words = recovery_phrase.split()

        run_script(
            driver,
            "inputRecoveryPhrase.js",
            args={"recovery_words": recovery_words},
        )

        recovery_phrase_confirm_xpath = "//*[@data-testid='recovery-phrase-confirm']"
        recovery_phrase_confirm_button = wait.until(
            EC.presence_of_element_located((By.XPATH, recovery_phrase_confirm_xpath))
        )

        recovery_phrase_confirm_button.click()

    # ? Wallet creation completion section
    wait.until(EC.url_contains("completion"))

    if "completion" in driver.current_url:
        wrapper_xpath = "//*[@data-testid='creation-successful']"
        wait.until(EC.presence_of_element_located((By.XPATH, wrapper_xpath)))

        onboarding_complete_done = "//*[@data-testid='onboarding-complete-done']"

        wait.until(
            EC.presence_of_element_located((By.XPATH, onboarding_complete_done))
        ).click()

    # ? Pin extension section
    wait.until(EC.url_contains("pin-extension"))

    if "pin-extension" in driver.current_url:
        next_button_xpath = "//*[@data-testid='pin-extension-next']"
        wait.until(
            EC.presence_of_element_located((By.XPATH, next_button_xpath))
        ).click()

        done_button_xpath = "//*[@data-testid='pin-extension-done']"
        wait.until(
            EC.presence_of_element_located((By.XPATH, done_button_xpath))
        ).click()

    # ? Back to home section
    wait.until(EC.url_contains("home"))
    if "home.html" in driver.current_url:
        wait.until(lambda driver: run_script(driver, "readyState.js"))
        wait.until(lambda driver: run_script(driver, "buttonTooltipClose.js"))


def onboarding_import_wallet(driver: webdriver, password: str):
    button_xpath = "//*[@data-testid='onboarding-import-wallet']"


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

    # ! TODO validate private key
    account = Web3().eth.account.from_key(private_key)
    ethereum_address = account.address

    extension_url = get_extension_home_url()
    driver.get(extension_url)

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(EC.url_to_be(extension_url))
    wait.until(lambda driver: run_script(driver, "readyState.js"))

    def open_account_menu(trigger: WebElement) -> WebElement:
        trigger.click()

        return wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section[role='dialog']"))
        )

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

    account_menu_button_xpath = "//*[@data-testid='account-menu-icon']"
    account_menu_button = wait.until(
        EC.presence_of_element_located((By.XPATH, account_menu_button_xpath))
    )

    account_menu_dialog = open_account_menu(account_menu_button)
    add_account(account_menu_dialog)

    return ethereum_address


def onboard_extension(
    driver: webdriver, import_with_recovery_phrase: bool = False
) -> webdriver:
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

        def accept_terms_of_use(locator: WebElement):
            if not locator.is_selected():
                locator.click()

        xpath = "//*[@id='onboarding__terms-checkbox']"
        terms_checkbox = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

        accept_terms_of_use(terms_checkbox)
    else:
        raise Exception("Failed to verify password")

    if import_with_recovery_phrase:
        onboarding_import_wallet(driver, password)
    else:
        onboarding_create_wallet(driver, password)

    print("Onboarding complete")
    return driver


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
        run_script(driver, "inputNetworkDetails.js", args={"network": network})
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
