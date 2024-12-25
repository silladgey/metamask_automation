import redis
import bcrypt

from utils.enums.credential import CredentialField, CredentialType


class SecureCredentialStorage:

    def __init__(
        self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0
    ):
        """Initialize Redis connection and set up credential storage system."""
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, db=redis_db, decode_responses=True
        )

    def _hash_and_store_credential(
        self, extension_name: str, key: CredentialField, credential: str
    ) -> str:
        """
        Hash and store a credential in Redis.
        This method takes an extension's name, a key, and a credential, hashes and stores the
        provided credential in Redis using a Redis hash with the extension name as the key.

        Args:
            extension_name (str): Unique identifier for the extension.
            key (str): Key to store the credential under.
            credential (str): Credential to hash and store.

        Returns:
            str: The hashed credential.
        """
        salt = bcrypt.gensalt()
        hashed_credential = bcrypt.hashpw(credential.encode("utf-8"), salt)
        self.redis.hset(
            f"extension:{extension_name}", key, hashed_credential.decode("utf-8")
        )
        return hashed_credential.decode("utf-8")

    def store_credentials(self, extension_name: str, credentials: dict) -> dict:
        """
        Hash and store a password or a recovery phrase in Redis.
        This method takes an extension's name and a dictionary containing a password and/or
        a recovery phrase, hashes and stores the provided credential(s) in Redis.
        The hashed credentials are then stored using a Redis hash with the extension name
        as the key.

        Args:
            extension_name (str): Unique identifier for the extension.
            credentials (dict): Dictionary containing either 'password' or
                                'recovery_phrase' or both.

        Returns:
            dict: The hashed credential(s).
        """

        if not credentials:
            return {}

        password = credentials.get(CredentialType.PASSWORD)
        recovery_phrase = credentials.get(CredentialType.RECOVERY_PHRASE)
        hashed_credentials = {}

        if password:
            hashed_credentials[CredentialType.PASSWORD] = (
                self._hash_and_store_credential(
                    extension_name, CredentialField.PASSWORD_HASH, password
                )
            )

        if recovery_phrase:
            hashed_credentials[CredentialType.RECOVERY_PHRASE] = (
                self._hash_and_store_credential(
                    extension_name,
                    CredentialField.RECOVERY_PHRASE_HASH,
                    recovery_phrase,
                )
            )

        return hashed_credentials

    def verify_credential(
        self, extension_name: str, key: CredentialField, credential: str
    ) -> bool:
        """
        Verify a password against stored hash.

        Args:
            extension_name (str): Unique identifier for the extension.
            key (str): Key to store the credential under.
            credential (str): Credential to hash and store.

        Returns:
            Boolean indicating if the credential matches
        """
        stored = self.redis.hget(f"extension:{extension_name}", key)
        if not stored:
            return False

        return bcrypt.checkpw(credential.encode("utf-8"), stored.encode("utf-8"))


if __name__ == "__main__":
    storage = SecureCredentialStorage()

    EXTENSION_NAME = "my-extension"
    PASSWORD = "mySecurePassword123!"
    RECOVERY_PHRASE = "we are only getting started baby"

    credentials = {"password": PASSWORD, "recovery_phrase": RECOVERY_PHRASE}
    hashed = storage.store_credentials(EXTENSION_NAME, credentials)

    print(f"Password Hash: {hashed.get(CredentialType.PASSWORD)}")
    print(f"Recovery Phrase Hash: {hashed.get(CredentialType.RECOVERY_PHRASE)}")

    # Verify password
    is_valid = storage.verify_credential(
        EXTENSION_NAME, CredentialField.PASSWORD_HASH, PASSWORD
    )
    print(f"Password Valid: {is_valid}")

    # Verify recovery phrase
    is_valid = storage.verify_credential(
        EXTENSION_NAME, CredentialField.RECOVERY_PHRASE_HASH, RECOVERY_PHRASE
    )
    print(f"Recovery Phrase Valid: {is_valid}")
