"""Пользовательские исключения для приложения."""


class CurrencyNotFoundError(Exception):
    """Выбрасывается, если код валюты неизвестен."""

    def __init__(self, code: str):
        super().__init__(f"Неизвестная валюта '{code}'")
        self.code = code


class InsufficientFundsError(Exception):
    """Выбрасывается при попытке снять больше средств, чем есть на балансе."""

    def __init__(self, available: float, required: float, code: str):
        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {code}, "
            f"требуется {required:.4f} {code}"
        )
        self.available = available
        self.required = required
        self.code = code


class ApiRequestError(Exception):
    """Выбрасывается при сбое внешнего API (или заглушки)."""

    def __init__(self, reason: str):
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
        self.reason = reason
