"""Decorators for logging and action confirmation."""

import logging
from functools import wraps
from pathlib import Path

# Настройка логирования
LOG_DIR = Path(__file__).resolve().parents[4] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "actions.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


def log_action(action_name: str):
    """Декоратор для логирования действий пользователя."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # args[0] - это self (AppContext)
            username = (
                args[0].current_user.username if args[0].current_user else "Unknown"
            )
            logging.info(
                f"User '{username}' performed action: {action_name} with args {kwargs}"
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def confirm_action(prompt_message: str = "Вы уверены? [y/N]: "):
    """Декоратор для подтверждения критичных действий (например, продажа)."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = input(f"\n{prompt_message}").strip().lower()
            if response not in ("y", "yes", "да"):
                return "Действие отменено пользователем."
            return func(*args, **kwargs)

        return wrapper

    return decorator
