"""Command-line interface for the currency wallet."""

import shlex
import sys

from ..core.usecases import AppContext


def print_error(message: str) -> None:
    """Вывод сообщения об ошибке красным цветом (если терминал поддерживает)."""
    print(f"\033[91mОшибка: {message}\033[0m")


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

            # Безопасный парсинг команд через shlex
            parts = shlex.split(cmd_line)
            command = parts[0].lower()
            args = parts[1:]

            if command == "exit" or command == "quit":
                print("До свидания!")
                sys.exit(0)

            elif command == "help":
                print(
                    "Доступные команды:\n"
                    "  register --username <name> --password <pass>  : Регистрация\n"
                    "  login --username <name> --password <pass>     : Вход в систему\n"
                    "  logout                                        : Выход из системы\n"
                    "  show-portfolio [--base <curr>]                : Показать портфель\n"
                    "  buy --currency <curr> --amount <num>          : Купить валюту\n"
                    "  sell --currency <curr> --amount <num>         : Продать валюту\n"
                    "  get-rate --from <curr> --to <curr>            : Узнать курс\n"
                    "  exit                                          : Выход"
                )

            elif command == "register":
                username = password = None
                for i in range(0, len(args), 2):
                    if args[i] == "--username" and i + 1 < len(args):
                        username = args[i + 1]
                    elif args[i] == "--password" and i + 1 < len(args):
                        password = args[i + 1]

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
                username = password = None
                for i in range(0, len(args), 2):
                    if args[i] == "--username" and i + 1 < len(args):
                        username = args[i + 1]
                    elif args[i] == "--password" and i + 1 < len(args):
                        password = args[i + 1]

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
                base = "USD"
                for i in range(0, len(args), 2):
                    if args[i] == "--base" and i + 1 < len(args):
                        base = args[i + 1]
                try:
                    print(context.show_portfolio(base))
                except ValueError as e:
                    print_error(str(e))

            elif command == "buy":
                currency = None
                amount = 0.0
                for i in range(0, len(args), 2):
                    if args[i] == "--currency" and i + 1 < len(args):
                        currency = args[i + 1]
                    elif args[i] == "--amount" and i + 1 < len(args):
                        try:
                            amount = float(args[i + 1])
                        except ValueError:
                            print_error("'amount' должен быть числом")
                            continue

                if not currency or amount <= 0:
                    print_error("Использование: buy --currency <curr> --amount <num>")
                    continue

                try:
                    print(context.buy(currency, amount))
                except ValueError as e:
                    print_error(str(e))

            elif command == "sell":
                currency = None
                amount = 0.0
                for i in range(0, len(args), 2):
                    if args[i] == "--currency" and i + 1 < len(args):
                        currency = args[i + 1]
                    elif args[i] == "--amount" and i + 1 < len(args):
                        try:
                            amount = float(args[i + 1])
                        except ValueError:
                            print_error("'amount' должен быть числом")
                            continue

                if not currency or amount <= 0:
                    print_error("Использование: sell --currency <curr> --amount <num>")
                    continue

                try:
                    print(context.sell(currency, amount))
                except ValueError as e:
                    print_error(str(e))

            elif command == "get-rate":
                from_curr = to_curr = None
                for i in range(0, len(args), 2):
                    if args[i] == "--from" and i + 1 < len(args):
                        from_curr = args[i + 1]
                    elif args[i] == "--to" and i + 1 < len(args):
                        to_curr = args[i + 1]

                if not from_curr or not to_curr:
                    print_error("Использование: get-rate --from <curr> --to <curr>")
                    continue

                try:
                    print(context.get_rate(from_curr, to_curr))
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
