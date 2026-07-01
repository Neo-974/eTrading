"""Chiffrement local des clés API avec Fernet (cryptography).

La clé maîtresse est générée automatiquement au premier lancement et stockée
dans `master.key` (voir config.MASTER_KEY_PATH). Ne jamais committer ce fichier.
"""
import os

from cryptography.fernet import Fernet

from config import settings


def _load_or_create_key() -> bytes:
    if os.path.exists(settings.MASTER_KEY_PATH):
        with open(settings.MASTER_KEY_PATH, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(settings.MASTER_KEY_PATH, "wb") as f:
        f.write(key)
    return key


_fernet = Fernet(_load_or_create_key())


def encrypt(value: str) -> str:
    if not value:
        return ""
    return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(value: str) -> str:
    if not value:
        return ""
    return _fernet.decrypt(value.encode("utf-8")).decode("utf-8")
