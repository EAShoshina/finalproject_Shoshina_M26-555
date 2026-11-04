"""Utility functions for data storage and cryptography."""

import hashlib
import json
import secrets
from pathlib import Path
from typing import Any

# Определяем путь к папке data
# (4 уровня вверх от utils.py: core -> package -> src -> root)
DATA_DIR = Path(__file__).resolve().parents[4] / "data"


def _get_file_path(filename: str) -> Path:
    """Возвращает полный путь к файлу в папке data."""
    return DATA_DIR / filename


def load_json(filename: str) -> Any:
    """Загружает данные из JSON-файла."""
    filepath = _get_file_path(filename)
    if not filepath.exists():
        return [] if filename != "rates.json" else {}
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data: Any) -> None:
    """Сохраняет данные в JSON-файл."""
    filepath = _get_file_path(filename)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def hash_password(password: str, salt: str) -> str:
    """Создает односторонний псевдо-хеш пароля."""
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def generate_salt() -> str:
    """Генерирует криптографически стойкую соль."""
    return secrets.token_hex(8)
