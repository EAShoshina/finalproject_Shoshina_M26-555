"""Utility functions for cryptography."""

import hashlib
import secrets


def hash_password(password: str, salt: str) -> str:
    """Создает односторонний псевдо-хеш пароля."""
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def generate_salt() -> str:
    """Генерирует криптографически стойкую соль."""
    return secrets.token_hex(8)
