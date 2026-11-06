"""Singleton для абстракции над JSON-хранилищем."""

import json
from typing import Any

from .settings import settings


class DatabaseManager:
    """
    Singleton для работы с JSON-файлами.
    Гарантирует централизованный доступ к данным и создание
    директорий при необходимости.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    def load(self, filename: str) -> Any:
        """Загружает JSON-файл из data/."""
        filepath = settings.data_dir / filename
        if not filepath.exists():
            return [] if filename != "rates.json" else {}
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    def save(self, filename: str, data: Any) -> None:
        """Атомарно сохраняет данные в JSON-файл (tmp → replace)."""
        filepath = settings.data_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(filepath)


# Глобальный экземпляр
db = DatabaseManager()
