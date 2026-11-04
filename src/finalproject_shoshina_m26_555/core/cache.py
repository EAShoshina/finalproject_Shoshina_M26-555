"""Caching mechanism using closures."""

import time
from collections.abc import Callable
from typing import Any


def rate_cache(ttl_seconds: int = 300) -> Callable:
    """
    Декоратор-замыкание для кэширования результатов функции
    на заданное время (по умолчанию 5 минут).
    """
    # Переменная замыкания, сохраняющая состояние между вызовами
    cache: dict[tuple[str, str], tuple[float, float]] = {}

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            # args[0] - это 'self' (AppContext), args[1] - from_curr, args[2] - to_curr
            from_curr = args[1]
            to_curr = args[2]

            key = (from_curr.upper(), to_curr.upper())
            current_time = time.time()

            # Если ключ есть в кэше и время не истекло
            if key in cache:
                cached_value, timestamp = cache[key]
                if current_time - timestamp < ttl_seconds:
                    return cached_value

            # Иначе вызываем оригинальную функцию и сохраняем результат
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result

        return wrapper

    return decorator
