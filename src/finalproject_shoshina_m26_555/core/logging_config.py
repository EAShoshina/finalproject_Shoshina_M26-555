"""Настройка конфигурации логирования с ротацией."""

import logging
from logging.handlers import RotatingFileHandler

from ..infra.settings import settings


def setup_logging() -> logging.Logger:
    """Настраивает логгер с ротацией файлов."""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = settings.logs_dir / "actions.log"

    log_format = "%(levelname)s %(asctime)s %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S"

    handler = RotatingFileHandler(
        log_file,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    logger = logging.getLogger("ValutaTrade")
    logger.setLevel(getattr(logging, settings.log_level))

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


logger = setup_logging()
