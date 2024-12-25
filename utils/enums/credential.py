from enum import StrEnum


class CredentialType(StrEnum):
    PASSWORD = "password"
    RECOVERY_PHRASE = "recovery_phrase"


class CredentialField(StrEnum):
    PASSWORD_HASH = "password_hash"
    RECOVERY_PHRASE_HASH = "recovery_phrase_hash"
