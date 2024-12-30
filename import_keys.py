from getpass import getpass
from web3 import Web3

from utils.constants.strings import TRIPLE_DOT


def import_web3_address() -> str:
    while True:
        try:
            private_key = getpass("Enter your private key: ")

            account = Web3().eth.account.from_key(private_key)
            ethereum_address = account.address

            print(f"Importing account {ethereum_address}{TRIPLE_DOT}")
            return ethereum_address
        except Exception as e:
            print(f"{e}. Please try again.")


if __name__ == "__main__":
    import_web3_address()
