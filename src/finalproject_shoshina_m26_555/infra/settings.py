"""Singleton для загрузки и кэширования конфигурации."""

from pathlib import Path


class SettingsLoader:
    """
    Singleton конфигурации.
    Реализован через __new__ для гарантии единственного экземпляра
    в памяти приложения. Это простой и читаемый способ, исключающий
    создание дополнительных экземпляров при импортах.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Базовые пути (4 уровня вверх от settings.py)
        self.base_dir = Path(__file__).resolve().parents[3]
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        # Параметры по умолчанию
        self.rates_ttl_seconds = 300
        self.default_base_currency = "USD"
        self.log_level = "INFO"

        # Логирование
        self.log_max_bytes = 5 * 1024 * 1024
        self.log_backup_count = 3

        # Валидация
        self.min_password_length = 4

        # Заглушки курсов (fallback, если rates.json пуст)
        self.fallback_rates = {
            "USD": 1.0,
            "EUR": 1.0786,
            "BTC": 59337.21,
            "RUB": 0.01016,
            "ETH": 3720.00,
            "SOL": 150.0,
        }

        self._initialized = True

    def get(self, key: str, default=None):
        """Возвращает значение настройки по ключу или default."""
        return getattr(self, key, default)

    def reload(self):
        """Перезагружает конфигурацию (сбрасывает и инициализирует заново)."""
        self._initialized = False
        self.__init__()


# Глобальный экземпляр
settings = SettingsLoader()
