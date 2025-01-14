from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.constants.prompts import CONFIRM_PASSWORD_TEXT
from utils.enums.metamask_extension import SupportedVersion
from utils.inputs import get_password

from storage.extension import ExtensionStorage

from credentials import SecureCredentialStorage
from setup import run_script, setup_chrome_driver_for_metamask

DEFAULT_TIMEOUT = 100


def get_extension_home_url() -> str:
    storage = ExtensionStorage()

    extension_url = storage.get_extension_base_url("metamask")
    return extension_url + "/home.html"


def click_element(driver: webdriver.Chrome, xpath: str):
    elem = driver.find_element(By.XPATH, xpath)
    if elem:
        elem.click()


# * SELENIUM HELPER FUNCTION
def get_open_tabs(driver: webdriver.Chrome) -> list:
    return driver.window_handles


# * SELENIUM HELPER FUNTION
def close_tab(driver: webdriver.Chrome, tab_index: int) -> None:
    driver.switch_to.window(driver.window_handles[tab_index])
    driver.close()


def create_a_new_wallet(driver: webdriver.Chrome, password: str):
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

            run_script(driver, "button-tooltip-close.js", args={})

            extension_url = get_extension_home_url()
            driver.get(extension_url)

        # ? added exception
        except Exception as e:
            print(e)


def import_an_existing_wallet(driver: webdriver.Chrome):
    button_xpath = "//*[@id='app-content']/div/div[2]/div/div/div/ul/li[3]/button"
    click_element(driver, button_xpath)


def import_private_key(driver: webdriver.Chrome, private_key: str) -> str:
    # returns a string of the account address
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

        return ethereum_address

    except Exception as e:
        print(e)


def onboard(driver: webdriver.Chrome) -> None:
    extension_url = get_extension_home_url()

    wait = WebDriverWait(driver, timeout=DEFAULT_TIMEOUT)
    wait.until(lambda driver: len(driver.window_handles) > 1)

    all_tabs = driver.window_handles

    print(f"There are {len(all_tabs)} tabs open")
    for index, tab in enumerate(all_tabs):
        driver.switch_to.window(tab)
        print(f"Tab {index + 1}: {driver.title}")

    for tab in all_tabs:
        if "home.html" not in driver.current_url:
            driver.switch_to.window(tab)
            print(driver.current_url)

    driver.get(extension_url)

    wait.until(
        lambda driver: driver.execute_script("return document.readyState == 'complete'")
    )

    print("Onboarding...")

    storage = SecureCredentialStorage()

    password = get_password(CONFIRM_PASSWORD_TEXT)
    verified = storage.verify_credential("metamask", "password_hash", password)

    if verified:
        click_element(driver, "//*[@id='onboarding__terms-checkbox']")
        create_a_new_wallet(driver, password)

        print("Onboarding complete")
        return driver
    else:
        print("Onboarding failed")
        return None


def add_custom_network(driver: webdriver.Chrome, network: dict) -> None:
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


def switch_to_network(driver: webdriver.Chrome, network_name: str) -> None:
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


def main():

    options = Options()
    service = Service()

    driver = setup_chrome_driver_for_metamask(
        options=options,
        service=service,
        metamask_version=SupportedVersion.LATEST,
        headless=False,
    )

    onboard(driver)

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
