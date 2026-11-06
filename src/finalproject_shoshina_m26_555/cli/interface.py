"""Command-line interface for the currency wallet."""

import json
import shlex
import sys
from typing import Any

from prettytable import PrettyTable

from ..core.usecases import AppContext
from ..exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from ..parser_service.config import ParserConfig
from ..parser_service.storage import ParserStorage
from ..parser_service.updater import RatesUpdater


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
                    "  update-rates [--source <src>]                 : Обновить курсы\n"
                    "  show-rates [--currency <curr>] [--top <n>]    : Показать курсы\n"
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
                except (ValueError, ApiRequestError, CurrencyNotFoundError) as e:
                    print_error(str(e))

            elif command == "buy":
                currency = kwargs.get("currency")
                amount_str = kwargs.get("amount")

                if not currency or not amount_str:
                    print_error("Использование: buy --currency <curr> --amount <num>")
                    continue

                try:
                    amount = float(amount_str)
                except ValueError:
                    print_error("'amount' должен быть числом")
                    continue

                try:
                    print(context.buy(currency=currency, amount=amount))
                except (
                    ValueError,
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
                except ValueError:
                    print_error("'amount' должен быть числом")
                    continue

                try:
                    print(context.sell(currency=currency, amount=amount))
                except (
                    ValueError,
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
                    print_error(
                        f"{e}. Поддерживаемые коды: "
                        f"USD, EUR, RUB, BTC, ETH, SOL"
                    )
                except ApiRequestError as e:
                    print_error(
                        f"{e}. Повторите попытку позже или проверьте сеть."
                    )
                except ValueError as e:
                    print_error(str(e))

            elif command == "update-rates":
                source = kwargs.get("source")
                if source and source.lower() not in ("coingecko", "exchangerate"):
                    print_error("Источник должен быть 'coingecko' или 'exchangerate'")
                    continue

                try:
                    config = ParserConfig()
                    storage = ParserStorage(config)
                    updater = RatesUpdater(config, storage)
                    result = updater.run_update(source_filter=source)

                    if result["success"]:
                        print(
                            f"Update successful. Total rates updated: "
                            f"{result['rates_count']}."
                        )
                    else:
                        print(
                            "Update completed with errors. "
                            "Check logs/actions.log for details."
                        )
                        for err in result["errors"]:
                            print_error(err)
                except ApiRequestError as e:
                    print_error(str(e))
                except OSError as e:
                    print_error(f"Ошибка записи rates.json: {e}")

            elif command == "show-rates":
                currency_filter = kwargs.get("currency")
                top_n_str = kwargs.get("top")

                try:
                    top_n = int(top_n_str) if top_n_str else None
                except ValueError:
                    print_error("Аргумент --top должен быть числом")
                    continue

                config = ParserConfig()
                if not config.rates_file_path.exists():
                    print_error(
                        "Локальный кеш курсов пуст. "
                        "Выполните 'update-rates', чтобы загрузить данные."
                    )
                    continue

                try:
                    with open(config.rates_file_path, encoding="utf-8") as f:
                        data = json.load(f)
                except (OSError, json.JSONDecodeError) as e:
                    print_error(f"Не удалось прочитать rates.json: {e}")
                    continue

                pairs = data.get("pairs", {})
                last_refresh = data.get("last_refresh", "неизвестно")

                if not pairs:
                    print("Кеш пуст.")
                    continue

                filtered_pairs = {}
                for pair, info in pairs.items():
                    if currency_filter and currency_filter.upper() not in pair:
                        continue
                    filtered_pairs[pair] = info

                if not filtered_pairs:
                    print_error(f"Курс для '{currency_filter}' не найден в кеше.")
                    continue

                if top_n:
                    sorted_pairs = sorted(
                        filtered_pairs.items(),
                        key=lambda x: x[1]["rate"],
                        reverse=True,
                    )[:top_n]
                else:
                    sorted_pairs = sorted(filtered_pairs.items())

                table = PrettyTable()
                table.field_names = ["Пара", "Курс", "Обновлено", "Источник"]
                table.align = "r"
                table.align["Пара"] = "l"

                for pair, info in sorted_pairs:
                    table.add_row(
                        [
                            pair,
                            f"{info['rate']:.6f}",
                            info["updated_at"][:19],
                            info["source"],
                        ]
                    )

                print(f"Rates from cache (last refresh: {last_refresh[:19]}):")
                print(table.get_string())

            else:
                print_error(
                    f"Неизвестная команда: '{command}'. Введите 'help' для справки."
                )
        except KeyboardInterrupt:
            print("\nДо свидания!")
            sys.exit(0)


if __name__ == "__main__":
    main()
