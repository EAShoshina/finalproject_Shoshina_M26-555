"""Клиенты для взаимодействия с внешними API."""

from abc import ABC, abstractmethod

import requests

from ..exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API-клиентов."""

    def __init__(self, config: ParserConfig):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> dict[str, float]:
        """Возвращает словарь курсов в формате {'PAIR': rate}."""
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для получения курсов криптовалют."""

    def fetch_rates(self) -> dict[str, float]:
        ids = ",".join(
            self.config.crypto_id_map[code] for code in self.config.crypto_currencies
        )
        url = (
            f"{self.config.coingecko_url}"
            f"?ids={ids}&vs_currencies={self.config.base_currency.lower()}"
        )

        try:
            response = requests.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko network error: {e}") from e

        rates = {}
        for code, crypto_id in self.config.crypto_id_map.items():
            if (
                crypto_id in data
                and self.config.base_currency.lower() in data[crypto_id]
            ):
                pair = f"{code}_{self.config.base_currency}"
                rates[pair] = float(data[crypto_id][self.config.base_currency.lower()])

        return rates


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для получения курсов фиатных валют."""

    def fetch_rates(self) -> dict[str, float]:
        url = (
            f"{self.config.exchangerate_api_url}"
            f"/{self.config.exchangerate_api_key}"
            f"/latest/{self.config.base_currency}"
        )

        try:
            response = requests.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                raise ApiRequestError(
                    f"ExchangeRate-API error: {data.get('error-type', 'Unknown')}"
                )
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API network error: {e}") from e

        rates = {}
        api_rates = data.get("rates", {})

        # Добавляем саму базовую валюту
        rates[f"{self.config.base_currency}_{self.config.base_currency}"] = 1.0

        for fiat in self.config.fiat_currencies:
            if fiat in api_rates:
                # API дает курс USD->EUR. Нам нужен EUR->USD, поэтому инвертируем
                rate = 1.0 / float(api_rates[fiat])
                rates[f"{fiat}_{self.config.base_currency}"] = rate

        return rates
