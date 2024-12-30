from getpass import getpass

from secrets import compare_digest

from utils.constants.prompts import (
    CONFIRM_PASSWORD_TEXT,
    ENTER_PASSWORD_TEXT,
)

from utils.validators import validate_password_input, is_valid


def get_password(prompt: str = ENTER_PASSWORD_TEXT) -> str:
    password = getpass(prompt)
    return validate_password_input(password, prompt)


def confirm_password(password: str, prompt: str = CONFIRM_PASSWORD_TEXT) -> bool:
    if not is_valid(password):
        return False

    confirm = getpass(prompt)
    confirm = validate_password_input(confirm, prompt)
    return compare_digest(password, confirm)
