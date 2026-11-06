"""Координатор процесса обновления курсов."""

import logging
from typing import Any

from ..exceptions import ApiRequestError
from .api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import ParserStorage

logger = logging.getLogger("ValutaTrade")


class RatesUpdater:
    """Точка входа для логики парсинга курсов."""

    SOURCE_NAMES = {
        "CoinGeckoClient": "coingecko",
        "ExchangeRateApiClient": "exchangerate",
    }

    def __init__(self, config: ParserConfig, storage: ParserStorage):
        self.config = config
        self.storage = storage
        self.clients: list[BaseApiClient] = [
            CoinGeckoClient(config),
            ExchangeRateApiClient(config),
        ]

    def run_update(self, source_filter: str | None = None) -> dict[str, Any]:
        """
        Запускает обновление курсов.
        source_filter: 'coingecko', 'exchangerate' или None (все).
        """
        logger.info("Starting rates update...")
        all_rates = {}
        errors = []

        for client in self.clients:
            cls_name = client.__class__.__name__
            client_name = self.SOURCE_NAMES.get(cls_name, cls_name)

            if source_filter and client_name != source_filter.lower():
                continue

            logger.info(f"Fetching from {client_name}...")
            try:
                rates = client.fetch_rates()
                all_rates.update(rates)
                logger.info(f"OK ({len(rates)} rates from {client_name})")
            except ApiRequestError as e:
                error_msg = f"Failed to fetch from {client_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        if not all_rates:
            if errors:
                logger.error("No rates fetched. Errors: %s", errors)
                return {
                    "success": False,
                    "rates_count": 0,
                    "errors": errors,
                }
            raise ApiRequestError("No rates fetched. Check network or API limits.")

        primary_source = "CoinGecko" if "BTC_USD" in all_rates else "ExchangeRate-API"

        logger.info(f"Writing {len(all_rates)} rates to cache...")
        self.storage.save_rates_snapshot(all_rates, primary_source)
        self.storage.append_to_history(all_rates, primary_source)

        return {
            "success": len(errors) == 0,
            "rates_count": len(all_rates),
            "errors": errors,
        }
