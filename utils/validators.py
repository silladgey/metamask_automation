import getpass

from utils.constants.prompts import PASSWORD_IS_EMPTY_TEXT, PASSWORD_NOT_IS_EMPTY_TEXT


def is_empty(text: str) -> bool:
    return not text or text.strip() == str("")


def is_lengthy(text: str) -> bool:
    return len(text.strip()) >= 8


def is_valid(text: str) -> bool:
    return not is_empty(text) and is_lengthy(text)


def match(text: str, text_to_confirm: str) -> bool:
    return text.strip() == text_to_confirm.strip()


def validate_password_input(text: str, prompt: str) -> str:
    while not is_valid(text):
        if is_empty(text):
            print(PASSWORD_IS_EMPTY_TEXT)
        elif not is_lengthy(text):
            print(PASSWORD_NOT_IS_EMPTY_TEXT)

        text = getpass.getpass(prompt)

    return text
