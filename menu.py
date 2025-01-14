from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from utils.constants.menu_items import (
    CREATE_A_NEW_WALLET_MENU_ITEM,
    IMPORT_AN_ACCOUNT_MENU_ITEM,
    IMPORT_AN_EXISTING_WALLET_MENU_ITEM,
    IMPORT_MULTIPLE_ACCOUNTS_MENU_ITEM,
    LIST_ACCOUNTS_IN_WALLET_MENU_ITEM,
    QUIT_MENU_ITEM,
)
from utils.constants.prompts import ENTER_CHOICE_INPUT_TEXT
from utils.constants.strings import NOT_PASSWORD_CONFIRMED_TEXT
from utils.enums.metamask_extension import SupportedVersion
from utils.inputs import get_password, confirm_password

from storage.extension import ExtensionStorage
from credentials import SecureCredentialStorage
from automate import onboard
from setup import setup_chrome_driver_for_metamask


def menu():
    print(CREATE_A_NEW_WALLET_MENU_ITEM)
    print(IMPORT_AN_EXISTING_WALLET_MENU_ITEM)
    print(LIST_ACCOUNTS_IN_WALLET_MENU_ITEM)
    print(IMPORT_AN_ACCOUNT_MENU_ITEM)
    print(IMPORT_MULTIPLE_ACCOUNTS_MENU_ITEM)
    print(QUIT_MENU_ITEM)
    return input(ENTER_CHOICE_INPUT_TEXT)


if __name__ == "__main__":
    choice = menu()

    old_storage = SecureCredentialStorage()

    if choice == "1":
        EXTENSION_NAME = "metamask"

        password = get_password()
        password_confirmed = confirm_password(password)

        if password_confirmed:
            old_storage.store_credentials(EXTENSION_NAME, {"password": password})
            print("Password stored successfully")
        else:
            print(NOT_PASSWORD_CONFIRMED_TEXT)
            exit(1)

        options = Options()
        service = Service()
        storage = ExtensionStorage()

        driver = setup_chrome_driver_for_metamask(
            options=options,
            service=service,
            metamask_version=SupportedVersion.LATEST,
            headless=False,
        )
        onboard(driver)

    elif choice == "2":
        pass

    elif choice == "3":
        pass

    elif choice == "4":
        pass

    elif choice == "5":
        pass

    elif choice == "6":
        exit(0)

    else:
        print("Invalid choice")
        exit(1)
