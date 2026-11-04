"""Атомарные операции чтения/записи для Parser Service."""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import ParserConfig


class ParserStorage:
    """Управление файлами rates.json и exchange_rates.json."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def _atomic_write(self, filepath: Path, data: Any) -> None:
        """Атомарная запись: временный файл -> rename."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        dir_path = filepath.parent
        with tempfile.NamedTemporaryFile(
            "w", dir=dir_path, delete=False, encoding="utf-8", suffix=".tmp"
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_name = tmp_file.name

        Path(tmp_name).replace(filepath)

    def save_rates_snapshot(self, rates: dict[str, float], source: str) -> None:
        """Сохраняет текущий снимок курсов в rates.json."""
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        pairs = {}
        for pair, rate in rates.items():
            pairs[pair] = {
                "rate": rate,
                "updated_at": now_iso,
                "source": source,
            }

        snapshot = {
            "pairs": pairs,
            "last_refresh": now_iso,
        }
        self._atomic_write(self.config.rates_file_path, snapshot)

    def append_to_history(self, rates: dict[str, float], source: str) -> None:
        """Добавляет записи в журнал exchange_rates.json."""
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        history: list[dict[str, Any]] = []
        if self.config.history_file_path.exists():
            with open(self.config.history_file_path, encoding="utf-8") as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []

        existing_ids = {item["id"] for item in history}

        for pair, rate in rates.items():
            from_curr, to_curr = pair.split("_")
            record_id = f"{pair}_{now_iso}"

            if record_id not in existing_ids:
                record = {
                    "id": record_id,
                    "from_currency": from_curr,
                    "to_currency": to_curr,
                    "rate": rate,
                    "timestamp": now_iso,
                    "source": source,
                    "meta": {
                        "request_ms": 0,
                        "status_code": 200,
                    },
                }
                history.append(record)

        self._atomic_write(self.config.history_file_path, history)
