import redis


class ExtensionStorage:

    def __init__(
        self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0
    ):
        """Initialize Redis connection and set up credential storage system."""
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, db=redis_db, decode_responses=True
        )

    def store_extension(self, extension_name: str, extension_data: dict) -> str:
        """
        Store an extension in Redis.
        This method takes an extension's name and the path to the extension, and stores the
        extension in Redis using a Redis hash with the extension name as the key.

        Args:
            extension_name (str): Unique identifier for the extension.
            extension_data (dict): Path to the extension.

        Returns:
            str: The path to the stored extension.
        """

        self.redis.hset(
            f"extension:{extension_name}",
            "extension_id",
            extension_data["extension_id"],
        )
        self.redis.hset(
            f"extension:{extension_name}",
            "base_url",
            f"chrome-extension://{extension_data['extension_id']}/",
        )

    def get_extension_id(self, extension_name: str) -> str:
        """
        Get the ID of an extension in Redis.
        This method takes an extension's name and retrieves the ID of the extension from Redis.

        Args:
            extension_name (str): Unique identifier for the extension.

        Returns:
            str: The ID of the extension.
        """
        return self.redis.hget(f"extension:{extension_name}", "extension_id")


if __name__ == "__main__":
    storage = ExtensionStorage()

    storage.store_extension("metamask", {"extension_id": "abc123"})
    print(storage.get_extension_id("metamask"))
