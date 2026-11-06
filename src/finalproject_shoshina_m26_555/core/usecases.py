"""Business logic and use cases for the application."""

from datetime import UTC, datetime

from prettytable import PrettyTable

from ..exceptions import ApiRequestError
from ..infra.database import db
from ..infra.settings import settings
from .currencies import get_currency
from .decorators import confirm_action, log_action, rate_cache
from .models import Portfolio, User


class AppContext:
    """Хранит состояние приложения и текущую сессию."""

    def __init__(self):
        self.current_user: User | None = None
        self.current_portfolio: Portfolio | None = None

    def _get_next_user_id(self) -> int:
        users = db.load("users.json")
        if not users:
            return 1
        return max(u["user_id"] for u in users) + 1

    @log_action("REGISTER")
    def register(self, username: str, password: str) -> str:
        users = db.load("users.json")
        if any(u["username"].lower() == username.lower() for u in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        if len(password) < settings.min_password_length:
            raise ValueError(
                f"Пароль должен быть не короче "
                f"{settings.min_password_length} символов"
            )

        new_id = self._get_next_user_id()
        new_user = User(user_id=new_id, username=username, password=password)
        users.append(new_user.to_dict())
        db.save("users.json", users)

        portfolios = db.load("portfolios.json")
        portfolios.append({"user_id": new_id, "wallets": {}})
        db.save("portfolios.json", portfolios)

        return (
            f"Пользователь '{username}' зарегистрирован (id={new_id}). "
            f"Войдите: login --username {username} --password ****"
        )

    @log_action("LOGIN")
    def login(self, username: str, password: str) -> str:
        users = db.load("users.json")
        user_data = next(
            (u for u in users if u["username"].lower() == username.lower()),
            None,
        )

        if not user_data:
            raise ValueError(f"Пользователь '{username}' не найден")

        user = User.from_dict(user_data)
        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        self.current_user = user
        portfolios = db.load("portfolios.json")
        portfolio_data = next(
            (p for p in portfolios if p["user_id"] == user.user_id),
            {"user_id": user.user_id, "wallets": {}},
        )
        self.current_portfolio = Portfolio.from_dict(portfolio_data)

        return f"Вы вошли как '{username}'"

    def logout(self) -> str:
        if self.current_user:
            username = self.current_user.username
            self.current_user = None
            self.current_portfolio = None
            return f"Вы вышли из системы '{username}'"
        return "Вы не были авторизованы"

    def show_portfolio(self, base_currency: str = "USD") -> str:
        if not self.current_user or not self.current_portfolio:
            raise ValueError("Сначала выполните login")

        base = base_currency.upper()
        get_currency(base)

        wallets = self.current_portfolio.wallets
        if not wallets:
            return f"Портфель пользователя '{self.current_user.username}' пуст."

        table = PrettyTable()
        table.field_names = [
            "Валюта",
            "Баланс",
            f"Курс к {base}",
            f"Стоимость ({base})",
        ]
        table.align = "r"
        table.align["Валюта"] = "l"

        total_value = 0.0
        for wallet in wallets.values():
            if wallet.currency_code == base:
                rate = 1.0
            else:
                rate, _ = self._get_rate(wallet.currency_code, base)

            value_in_base = wallet.balance * rate
            total_value += value_in_base
            table.add_row(
                [
                    wallet.currency_code,
                    f"{wallet.balance:.4f}",
                    f"{rate:.4f}",
                    f"{value_in_base:,.2f}",
                ]
            )

        table.add_row(["ИТОГО", "", "", f"{total_value:,.2f} {base}"])
        return (
            f"Портфель пользователя '{self.current_user.username}' "
            f"(база: {base}):\n{table.get_string()}"
        )

    @log_action("BUY", verbose=True)
    def buy(self, currency: str, amount: float) -> str:
        if not self.current_user or not self.current_portfolio:
            raise ValueError("Сначала выполните login")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        currency_obj = get_currency(currency)
        currency_code = currency_obj.code

        try:
            wallet = self.current_portfolio.get_wallet(currency_code)
        except ValueError:
            self.current_portfolio.add_currency(currency_code)
            wallet = self.current_portfolio.get_wallet(currency_code)

        old_balance = wallet.balance
        wallet.deposit(amount)
        self._save_portfolio()

        rate, _ = self._get_rate(currency_code, "USD")
        cost_usd = amount * rate

        return (
            f"Покупка выполнена: {amount:.4f} {currency_code} "
            f"по курсу {rate:.2f} USD/{currency_code}\n"
            f"Изменения в портфеле:\n"
            f"- {currency_code}: было {old_balance:.4f} → "
            f"стало {wallet.balance:.4f}\n"
            f"Оценочная стоимость покупки: {cost_usd:,.2f} USD"
        )

    @confirm_action("Вы уверены, что хотите продать эту валюту? [y/N]: ")
    @log_action("SELL", verbose=True)
    def sell(self, currency: str, amount: float) -> str:
        if not self.current_user or not self.current_portfolio:
            raise ValueError("Сначала выполните login")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        currency_obj = get_currency(currency)
        currency_code = currency_obj.code

        wallet = self.current_portfolio.get_wallet(currency_code)

        old_balance = wallet.balance
        wallet.withdraw(amount)
        self._save_portfolio()

        rate, _ = self._get_rate(currency_code, "USD")
        revenue_usd = amount * rate

        return (
            f"Продажа выполнена: {amount:.4f} {currency_code} "
            f"по курсу {rate:.2f} USD/{currency_code}\n"
            f"Изменения в портфеле:\n"
            f"- {currency_code}: было {old_balance:.4f} → "
            f"стало {wallet.balance:.4f}\n"
            f"Оценочная выручка: {revenue_usd:,.2f} USD"
        )

    def get_rate(self, from_curr: str, to_curr: str) -> str:
        get_currency(from_curr)
        get_currency(to_curr)

        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        if from_curr == to_curr:
            return f"Курс {from_curr}→{to_curr}: 1.00000000 (встроенный)"

        rate, updated_at = self._get_rate(from_curr, to_curr)
        if rate is None or rate == 0.0:
            raise ApiRequestError("Сервис курсов временно недоступен")

        inverse_rate = 1.0 / rate if rate != 0 else 0.0
        return (
            f"Курс {from_curr}→{to_curr}: {rate:.8f} "
            f"(обновлено: {updated_at})\n"
            f"Обратный курс {to_curr}→{from_curr}: {inverse_rate:.8f}"
        )

    @rate_cache(ttl_seconds=settings.rates_ttl_seconds)
    def _get_rate(self, from_curr: str, to_curr: str) -> tuple[float, str]:
        """Внутренний метод получения курса.
        Возвращает кортеж (rate, updated_at)."""
        raw = db.load("rates.json")
        rates_data = raw.get("pairs", {}) if isinstance(raw, dict) else {}

        pair = f"{from_curr}_{to_curr}"
        if pair in rates_data and "rate" in rates_data[pair]:
            rate = float(rates_data[pair]["rate"])
            updated_at = rates_data[pair].get("updated_at", "неизвестно")
            return rate, updated_at

        inverse_pair = f"{to_curr}_{from_curr}"
        if inverse_pair in rates_data and "rate" in rates_data[inverse_pair]:
            rate = 1.0 / float(rates_data[inverse_pair]["rate"])
            updated_at = rates_data[inverse_pair].get("updated_at", "неизвестно")
            return rate, updated_at

        # Заглушка (имитация API)
        fallback_rates = settings.fallback_rates
        if from_curr in fallback_rates and to_curr in fallback_rates:
            rate = fallback_rates[from_curr] / fallback_rates[to_curr]
            updated_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            return rate, updated_at
        raise ApiRequestError(f"Не удалось получить курс для {from_curr}→{to_curr}")

    def _save_portfolio(self) -> None:
        if not self.current_portfolio:
            return
        portfolios = db.load("portfolios.json")
        for i, p in enumerate(portfolios):
            if p["user_id"] == self.current_portfolio.user_id:
                portfolios[i] = self.current_portfolio.to_dict()
                break
        db.save("portfolios.json", portfolios)
