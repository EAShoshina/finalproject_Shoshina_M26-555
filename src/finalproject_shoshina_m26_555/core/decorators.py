"""Декораторы для логирования и подтверждения действий."""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from .logging_config import logger


def log_action(action_name: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций.
    Не глотает исключения, а логирует их и пробрасывает дальше.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # args[0] - это self (AppContext)
            context = args[0]
            username = (
                context.current_user.username if context.current_user else "Unknown"
            )

            try:
                result = func(*args, **kwargs)

                # Формируем сообщение об успехе
                extra_info = ""
                if verbose and "currency" in kwargs and "amount" in kwargs:
                    extra_info = (
                        f" currency='{kwargs['currency']}' "
                        f"amount={kwargs['amount']:.4f}"
                    )

                log_msg = f"{action_name} user='{username}'{extra_info} result=OK"
                logger.info(log_msg)
                return result

            except Exception as e:
                # Логируем ошибку и пробрасываем дальше
                error_type = e.__class__.__name__
                log_msg = (
                    f"{action_name} user='{username}' result=ERROR "
                    f"error_type={error_type} error_message='{str(e)}'"
                )
                logger.error(log_msg)
                raise

        return wrapper

    return decorator


def confirm_action(prompt_message: str = "Вы уверены? [y/N]: "):
    """Декоратор для подтверждения критичных действий."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            response = input(f"\n{prompt_message}").strip().lower()
            if response not in ("y", "yes", "да"):
                return "Действие отменено пользователем."
            return func(*args, **kwargs)

        return wrapper

    return decorator


def rate_cache(ttl_seconds: int = 300) -> Callable:
    """Декоратор-замыкание для кэширования курсов."""
    cache: dict[tuple[str, str], tuple[float, float]] = {}

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            from_curr = args[1]
            to_curr = args[2]
            key = (from_curr.upper(), to_curr.upper())
            current_time = time.time()

            if key in cache:
                cached_value, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    return cached_value

            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result

        return wrapper

    return decorator
