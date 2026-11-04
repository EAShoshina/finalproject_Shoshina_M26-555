"""Конфигурация для Parser Service."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParserConfig:
    """Структурированное хранение настроек парсера."""

    # Ключ загружается из переменной окружения (или 'demo' для тестов)
    exchangerate_api_key: str = os.getenv("EXCHANGERATE_API_KEY", "demo")

    # Эндпоинты
    coingecko_url: str = "https://api.coingecko.com/api/v3/simple/price"
    exchangerate_api_url: str = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    base_currency: str = "USD"
    fiat_currencies: tuple = ("EUR", "GBP", "RUB")
    crypto_currencies: tuple = ("BTC", "ETH", "SOL")
    crypto_id_map: dict = field(
        default_factory=lambda: {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
        }
    )

    # Сетевые параметры
    request_timeout: int = 10

    @property
    def rates_file_path(self) -> Path:
        """Путь к data/rates.json."""
        return Path(__file__).resolve().parents[3] / "data" / "rates.json"

    @property
    def history_file_path(self) -> Path:
        """Путь к data/exchange_rates.json."""
        return Path(__file__).resolve().parents[3] / "data" / "exchange_rates.json"
