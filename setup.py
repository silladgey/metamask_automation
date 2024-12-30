import os
import shutil
import requests


def download_metamask_zip(version: str) -> None:
    """
    Download the MetaMask extension for a specific version

    Args:
        version (str): Version of the MetaMask extension to download
    """

    url = f"https://github.com/MetaMask/metamask-extension/releases/download/v{version}/metamask-chrome-{version}.zip"

    print(f"Retrieving MetaMask version {version} extension from {url}")

    extension_dir = os.path.join(os.getcwd(), "extension")
    extension_path = os.path.join(extension_dir, f"{version}.zip")

    if not os.path.exists(extension_dir):
        os.makedirs(extension_dir, exist_ok=True)

    if os.path.exists(extension_path):
        print(
            f"MetaMask version {version} extension already exists at location {extension_path}"
        )
        return

    with requests.get(url, stream=True, timeout=100) as response:
        response.raise_for_status()
        with open(extension_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)
