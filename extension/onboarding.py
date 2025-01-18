import pyperclip

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from extension.helpers import get_extension_home_url, run_script

from storage.extension import ExtensionStorage
from credentials import SecureCredentialStorage

from utils.constants.prompts import CONFIRM_PASSWORD_TEXT
from utils.constants.values import DEFAULT_TIMEOUT
from utils.inputs import get_password


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
        create_password_input = wait.until(
            EC.presence_of_element_located((By.XPATH, create_password_xpath))
        )

        if create_password_input.is_enabled():
            create_password_input.clear()
            create_password_input.send_keys(password)

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
    # ! TODO Implement import wallet functionality
    button_xpath = "//*[@data-testid='onboarding-import-wallet']"


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
