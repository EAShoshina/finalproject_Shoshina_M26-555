"""Command-line interface for the currency wallet."""

import shlex
import sys
from typing import Any

from ..core.usecases import AppContext
from ..exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)


def print_error(message: str) -> None:
    """Вывод сообщения об ошибке красным цветом."""
    print(f"\033[91mОшибка: {message}\033[0m")


def _parse_kwargs(args: list[str]) -> dict[str, Any]:
    """
    Вспомогательная функция для парсинга аргументов.
    Преобразует список ['--currency', 'BTC'] в словарь.
    """
    kwargs = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                kwargs[key] = args[i + 1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            i += 1
    return kwargs


def main() -> None:
    """Главный цикл консольного приложения."""
    context = AppContext()
    print("Добро пожаловать в Валютный Кошелек (ValutaTrade Hub)!")
    print("Введите 'help' для получения списка команд.")

    while True:
        try:
            cmd_line = input("\nwallet> ").strip()
            if not cmd_line:
                continue

            parts = shlex.split(cmd_line)
            command = parts[0].lower()
            args = parts[1:]
            kwargs = _parse_kwargs(args)

            if command in ("exit", "quit"):
                print("До свидания!")
                sys.exit(0)

            elif command == "help":
                print(
                    "Доступные команды:\n"
                    "  register --username <name> --password <pass>  : Регистрация\n"
                    "  login --username <name> --password <pass>     : Вход\n"
                    "  logout                                        : Выход\n"
                    "  show-portfolio [--base <curr>]                : Портфель\n"
                    "  buy --currency <curr> --amount <num>          : Купить\n"
                    "  sell --currency <curr> --amount <num>         : Продать\n"
                    "  get-rate --from <curr> --to <curr>            : Узнать курс\n"
                    "  exit                                          : Выход"
                )

            elif command == "register":
                username = kwargs.get("username")
                password = kwargs.get("password")
                if not username or not password:
                    print_error(
                        "Использование: register --username <name> --password <pass>"
                    )
                    continue
                try:
                    print(context.register(username, password))
                except ValueError as e:
                    print_error(str(e))

            elif command == "login":
                username = kwargs.get("username")
                password = kwargs.get("password")
                if not username or not password:
                    print_error(
                        "Использование: login --username <name> --password <pass>"
                    )
                    continue
                try:
                    print(context.login(username, password))
                except ValueError as e:
                    print_error(str(e))

            elif command == "logout":
                print(context.logout())

            elif command == "show-portfolio":
                base = kwargs.get("base", "USD")
                try:
                    print(context.show_portfolio(base))
                except ValueError as e:
                    print_error(str(e))

            elif command == "buy":
                currency = kwargs.get("currency")
                amount_str = kwargs.get("amount")

                if not currency or not amount_str:
                    print_error("Использование: buy --currency <curr> --amount <num>")
                    continue

                try:
                    amount = float(amount_str)
                    print(context.buy(currency, amount))
                except ValueError as e:
                    if "could not convert string to float" in str(e):
                        print_error("'amount' должен быть числом")
                    else:
                        print_error(str(e))
                except (
                    CurrencyNotFoundError,
                    InsufficientFundsError,
                    ApiRequestError,
                ) as e:
                    print_error(str(e))

            elif command == "sell":
                currency = kwargs.get("currency")
                amount_str = kwargs.get("amount")

                if not currency or not amount_str:
                    print_error("Использование: sell --currency <curr> --amount <num>")
                    continue

                try:
                    amount = float(amount_str)
                    result = context.sell(currency, amount)
                    print(result)
                except ValueError as e:
                    if "could not convert string to float" in str(e):
                        print_error("'amount' должен быть числом")
                    else:
                        print_error(str(e))
                except (
                    CurrencyNotFoundError,
                    InsufficientFundsError,
                    ApiRequestError,
                ) as e:
                    print_error(str(e))

            elif command == "get-rate":
                from_curr = kwargs.get("from")
                to_curr = kwargs.get("to")

                if not from_curr or not to_curr:
                    print_error("Использование: get-rate --from <curr> --to <curr>")
                    continue

                try:
                    print(context.get_rate(from_curr, to_curr))
                except CurrencyNotFoundError as e:
                    print_error(f"{e}. Поддерживаемые коды: USD, EUR, RUB, BTC, ETH")
                except ApiRequestError as e:
                    print_error(f"{e}. Повторите попытку позже или проверьте сеть.")
                except ValueError as e:
                    print_error(str(e))

            else:
                print_error(
                    f"Неизвестная команда: '{command}'. Введите 'help' для справки."
                )

        except KeyboardInterrupt:
            print("\nДо свидания!")
            sys.exit(0)
        except Exception as e:
            print_error(f"Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()
