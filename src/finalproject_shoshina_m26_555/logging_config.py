"""Настройка конфигурации логирования с ротацией."""

import logging
from logging.handlers import RotatingFileHandler

from .infra.settings import settings


def setup_logging():
    """Настраивает логгер с ротацией файлов."""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = settings.logs_dir / "actions.log"

    # Формат: INFO 2025-10-09T12:05:22 BUY user='alice' result=OK
    log_format = "%(levelname)s %(asctime)s %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S"

    # Ротация: макс 5 МБ, хранит 3 старых файла
    handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    logger = logging.getLogger("ValutaTrade")
    logger.setLevel(getattr(logging, settings.get("log_level", "INFO")))

    # Очищаем старые хендлеры, чтобы не дублировать при перезагрузке
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logging()
