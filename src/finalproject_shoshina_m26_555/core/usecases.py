"""Business logic and use cases for the application."""

from prettytable import PrettyTable

from .cache import rate_cache
from .decorators import confirm_action, log_action
from .models import Portfolio, User
from .utils import load_json, save_json


class AppContext:
    """Хранит состояние приложения и текущую сессию."""

    def __init__(self):
        self.current_user: User | None = None
        self.current_portfolio: Portfolio | None = None

    def _get_next_user_id(self) -> int:
        users = load_json("users.json")
        if not users:
            return 1
        return max(u["user_id"] for u in users) + 1

    def register(self, username: str, password: str) -> str:
        users = load_json("users.json")
        if any(u["username"].lower() == username.lower() for u in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        new_id = self._get_next_user_id()
        new_user = User(user_id=new_id, username=username, password=password)
        users.append(new_user.to_dict())
        save_json("users.json", users)

        portfolios = load_json("portfolios.json")
        portfolios.append({"user_id": new_id, "wallets": {}})
        save_json("portfolios.json", portfolios)

        return (
            f"Пользователь '{username}' зарегистрирован (id={new_id}). "
            f"Войдите: login --username {username} --password ****"
        )

    def login(self, username: str, password: str) -> str:
        users = load_json("users.json")
        user_data = next(
            (u for u in users if u["username"].lower() == username.lower()), None
        )

        if not user_data:
            raise ValueError(f"Пользователь '{username}' не найден")

        user = User.from_dict(user_data)
        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        self.current_user = user

        portfolios = load_json("portfolios.json")
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
        """Показывает портфель пользователя в виде красивой таблицы."""
        if not self.current_user or not self.current_portfolio:
            raise ValueError("Сначала выполните login")

        wallets = self.current_portfolio.wallets
        if not wallets:
            return f"Портфель пользователя '{self.current_user.username}' пуст."

        base = base_currency.upper()

        # Создаем таблицу
        table = PrettyTable()
        table.field_names = [
            "Валюта",
            "Баланс",
            f"Курс к {base}",
            f"Стоимость ({base})",
        ]

        # Выравнивание: текст слева, цифры справа
        table.align = "r"
        table.align["Валюта"] = "l"

        total_value = 0.0

        for wallet in wallets.values():
            if wallet.currency_code == base:
                rate = 1.0
            else:
                rate = self._get_rate(wallet.currency_code, base)

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

        # Добавляем строку ИТОГО
        table.add_row(["ИТОГО", "", "", f"{total_value:,.2f} {base}"])

        header = f"Портфель пользователя '{self.current_user.username}' (база: {base}):"
        return f"{header}\n{table.get_string()}"

    @log_action("BUY")
    def buy(self, currency: str, amount: float) -> str:
        if not self.current_user or not self.current_portfolio:
            raise ValueError("Сначала выполните login")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        currency = currency.upper()
        try:
            wallet = self.current_portfolio.get_wallet(currency)
        except ValueError:
            self.current_portfolio.add_currency(currency)
            wallet = self.current_portfolio.get_wallet(currency)

        old_balance = wallet.balance
        wallet.deposit(amount)
        self._save_portfolio()

        rate = self._get_rate(currency, "USD")
        cost_usd = amount * rate

        return (
            f"Покупка выполнена: {amount:.4f} {currency} "
            f"по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
            f"Оценочная стоимость покупки: {cost_usd:,.2f} USD"
        )

    @log_action("SELL")
    @confirm_action("Вы уверены, что хотите продать эту валюту? [y/N]: ")
    def sell(self, currency: str, amount: float) -> str:
        if not self.current_user or not self.current_portfolio:
            raise ValueError("Сначала выполните login")
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        currency = currency.upper()
        wallet = self.current_portfolio.get_wallet(currency)

        old_balance = wallet.balance
        wallet.withdraw(amount)
        self._save_portfolio()

        rate = self._get_rate(currency, "USD")
        revenue_usd = amount * rate

        return (
            f"Продажа выполнена: {amount:.4f} {currency} "
            f"по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"- {currency}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
            f"Оценочная выручка: {revenue_usd:,.2f} USD"
        )

    def get_rate(self, from_curr: str, to_curr: str) -> str:
        from_curr = from_curr.upper()
        to_curr = to_curr.upper()

        if from_curr == to_curr:
            return f"Курс {from_curr}→{to_curr}: 1.00000000 (встроенный)"

        rate = self._get_rate(from_curr, to_curr)
        if rate is None or rate == 0.0:
            raise ValueError(
                f"Курс {from_curr}→{to_curr} недоступен. Повторите попытку позже."
            )

        inverse_rate = 1.0 / rate if rate != 0 else 0.0
        return (
            f"Курс {from_curr}→{to_curr}: {rate:.8f}\n"
            f"Обратный курс {to_curr}→{from_curr}: {inverse_rate:.2f}"
        )

    @rate_cache(ttl_seconds=300)
    def _get_rate(self, from_curr: str, to_curr: str) -> float:
        """Внутренний метод получения курса (с заглушкой)."""
        rates_data = load_json("rates.json")

        if not isinstance(rates_data, dict):
            rates_data = {}

        pair = f"{from_curr}_{to_curr}"
        if pair in rates_data and "rate" in rates_data[pair]:
            return float(rates_data[pair]["rate"])

        inverse_pair = f"{to_curr}_{from_curr}"
        if inverse_pair in rates_data and "rate" in rates_data[inverse_pair]:
            return 1.0 / float(rates_data[inverse_pair]["rate"])

        fallback_rates = {
            "USD": 1.0,
            "EUR": 1.0786,
            "BTC": 59337.21,
            "RUB": 0.01016,
            "ETH": 3720.00,
        }

        if from_curr in fallback_rates and to_curr in fallback_rates:
            return fallback_rates[from_curr] / fallback_rates[to_curr]

        return 0.0

    def _save_portfolio(self) -> None:
        """Сохраняет текущий портфель в JSON."""
        if not self.current_portfolio:
            return
        portfolios = load_json("portfolios.json")
        for i, p in enumerate(portfolios):
            if p["user_id"] == self.current_portfolio.user_id:
                portfolios[i] = self.current_portfolio.to_dict()
                break
        save_json("portfolios.json", portfolios)
