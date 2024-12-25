import getpass

from secrets import compare_digest

from utils.constants.menu_items import (
    CREATE_A_NEW_WALLET_MENU_ITEM,
    IMPORT_AN_ACCOUNT_MENU_ITEM,
    IMPORT_AN_EXISTING_WALLET_MENU_ITEM,
    IMPORT_MULTIPLE_ACCOUNTS_MENU_ITEM,
    LIST_ACCOUNTS_IN_WALLET_MENU_ITEM,
    QUIT_MENU_ITEM,
)
from utils.constants.prompts import (
    CONFIRM_PASSWORD_TEXT,
    ENTER_CHOICE_INPUT_TEXT,
    ENTER_PASSWORD_TEXT,
    NOT_PASSWORD_CONFIRMED_TEXT,
)
from utils.validators import validate_password_input, is_valid


def menu():
    print(CREATE_A_NEW_WALLET_MENU_ITEM)
    print(IMPORT_AN_EXISTING_WALLET_MENU_ITEM)
    print(LIST_ACCOUNTS_IN_WALLET_MENU_ITEM)
    print(IMPORT_AN_ACCOUNT_MENU_ITEM)
    print(IMPORT_MULTIPLE_ACCOUNTS_MENU_ITEM)
    print(QUIT_MENU_ITEM)
    return input(ENTER_CHOICE_INPUT_TEXT)


def get_password() -> str:
    password = getpass.getpass(ENTER_PASSWORD_TEXT)
    return validate_password_input(password, ENTER_PASSWORD_TEXT)


def confirm_password(password: str) -> bool:
    if not is_valid(password):
        return False

    confirm = getpass.getpass(CONFIRM_PASSWORD_TEXT)
    confirm = validate_password_input(confirm, CONFIRM_PASSWORD_TEXT)
    return compare_digest(password, confirm)


if __name__ == "__main__":
    choice = menu()

    password = get_password()
    password_confirmed = confirm_password(password)

    if not password_confirmed:
        print(NOT_PASSWORD_CONFIRMED_TEXT)
