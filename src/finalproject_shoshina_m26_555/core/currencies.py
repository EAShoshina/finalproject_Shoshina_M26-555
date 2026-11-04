"""Иерархия валют: ABC, наследники и фабрика."""

import re
from abc import ABC, abstractmethod

from ..exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для всех валют."""

    def __init__(self, name: str, code: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Имя валюты не может быть пустым")
        if not isinstance(code, str) or not re.match(r"^[A-Z]{2,5}$", code):
            raise ValueError(
                "Код валюты должен состоять из 2-5 заглавных латинских букв"
            )

        self.name = name.strip()
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Строковое представление для UI/логов."""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта."""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта."""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


# Реестр валют (Фабрика)
_REGISTRY: dict[str, type[Currency]] = {
    "USD": lambda: FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": lambda: FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": lambda: FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": lambda: CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": lambda: CryptoCurrency("Ethereum", "ETH", "Ethash", 4.50e11),
    "SOL": lambda: CryptoCurrency("Solana", "SOL", "PoH", 8.50e10),
}


def get_currency(code: str) -> Currency:
    """Фабричный метод для получения экземпляра валюты по коду."""
    code_upper = code.upper()
    if code_upper not in _REGISTRY:
        raise CurrencyNotFoundError(code_upper)
    return _REGISTRY[code_upper]()
