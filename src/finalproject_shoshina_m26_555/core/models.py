"""Domain models for the currency wallet."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..exceptions import InsufficientFundsError
from ..infra.settings import settings
from .utils import generate_salt, hash_password


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        password: str,
        salt: str | None = None,
        registration_date: str | None = None,
    ):
        self._user_id = user_id
        self.username = username  # Использует сеттер для валидации
        if (
            not isinstance(password, str)
            or len(password) < settings.min_password_length
        ):
            raise ValueError(
                f"Пароль должен быть не короче "
                f"{settings.min_password_length} символов"
            )

        self._salt = salt or generate_salt()
        self._hashed_password = hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.now().isoformat()

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя не может быть пустым")
        self._username = value.strip()

    @property
    def registration_date(self) -> str:
        return self._registration_date

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль на совпадение."""
        return hash_password(password, self._salt) == self._hashed_password

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя с хешированием."""
        if (
            not isinstance(new_password, str)
            or len(new_password) < settings.min_password_length
        ):
            raise ValueError(
                f"Пароль должен быть не короче "
                f"{settings.min_password_length} символов"
            )
        self._salt = generate_salt()
        self._hashed_password = hash_password(new_password, self._salt)

    def get_user_info(self) -> dict[str, Any]:
        """Возвращает информацию о пользователе (без пароля)."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date,
        }

    def to_dict(self) -> dict[str, Any]:
        """Сериализация для сохранения в JSON."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Десериализация из JSON."""
        user = cls.__new__(cls)
        user._user_id = data["user_id"]
        user._username = data["username"]
        user._hashed_password = data["hashed_password"]
        user._salt = data["salt"]
        user._registration_date = data["registration_date"]
        return user


class Wallet:
    """Кошелёк пользователя для одной конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self.balance = balance  # Использует сеттер для валидации

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """Пополнение баланса."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снятие средств."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        if amount > self.balance:
            raise InsufficientFundsError(
                available=self.balance,
                required=amount,
                code=self.currency_code,
            )
        self.balance -= amount

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self.balance:.4f}"

    def to_dict(self) -> dict[str, Any]:
        return {"currency_code": self.currency_code, "balance": self.balance}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Wallet":
        return cls(currency_code=data["currency_code"], balance=data["balance"])


class Portfolio:
    """Управление всеми кошельками одного пользователя."""

    def __init__(
        self, user_id: int, wallets_data: dict[str, dict[str, Any]] | None = None
    ):
        self._user_id = user_id
        self._wallets: dict[str, Wallet] = {}
        if wallets_data:
            for curr_code, data in wallets_data.items():
                self._wallets[curr_code.upper()] = Wallet.from_dict(data)

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> None:
        """Добавляет новый кошелёк в портфель."""
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {code} уже существует")
        self._wallets[code] = Wallet(currency_code=code)

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает объект Wallet по коду валюты."""
        code = currency_code.upper()
        if code not in self._wallets:
            raise ValueError(f"У вас нет кошелька '{code}'.")
        return self._wallets[code]

    def get_total_value(
        self,
        base_currency: str = "USD",
        get_rate_func: Callable[[str, str], float] | None = None,
    ) -> float:
        """Возвращает общую стоимость всех валют в base_currency."""
        total = 0.0
        base_code = base_currency.upper()

        fallback_rates = settings.fallback_rates

        for wallet in self._wallets.values():
            if wallet.currency_code == base_code:
                total += wallet.balance
            elif get_rate_func:
                total += wallet.balance * get_rate_func(
                    wallet.currency_code, base_code
                )
            elif (
                wallet.currency_code in fallback_rates
                and base_code in fallback_rates
            ):
                rate = (
                    fallback_rates[wallet.currency_code] / fallback_rates[base_code]
                )
                total += wallet.balance * rate
            else:
                raise ValueError(
                    f"Не удалось получить курс "
                    f"{wallet.currency_code}→{base_code}"
                )
        return total

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self._user_id,
            "wallets": {code: w.to_dict() for code, w in self._wallets.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Portfolio":
        return cls(user_id=data["user_id"], wallets_data=data.get("wallets", {}))
