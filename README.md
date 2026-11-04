# ValutaTrade Hub — Консольный валютный кошелёк

## 📖 Описание проекта

**ValutaTrade Hub** — это консольное приложение для управления виртуальным портфелем фиатных и криптовалют. Пользователи могут регистрироваться, совершать сделки по покупке/продаже, отслеживать актуальные курсы в реальном времени через интеграцию с внешними API.

### Ключевые возможности:
- 🔐 Регистрация и безопасный вход (хеширование паролей с солью через SHA-256)
- 💼 Управление портфелем: покупка/продажа валют с оценкой стоимости
- 📈 Отслеживание курсов через **CoinGecko** (крипто) и **ExchangeRate-API** (фиат)
- 📊 Красивый вывод данных в виде таблиц (`prettytable`)
- 📝 Логирование всех операций с ротацией файлов
- ✅ Подтверждение критичных действий (продажа)
- ⚡ Кэширование курсов (TTL) для экономии запросов к API

---

## 🏗️ Архитектура проекта

```text
finalproject_Shoshina_M26-555/
│
├── data/                          # Хранилище данных
│    ├── users.json                # Пользователи
│    ├── portfolios.json           # Портфели и кошельки
│    ├── rates.json                # Актуальные курсы (кэш для Core)
│    └── exchange_rates.json       # История курсов (Parser Service)
│
├── src/finalproject_shoshina_m26_555/
│    ├── __init__.py
│    ├── logging_config.py         # Настройка логирования с ротацией
│    ├── core/                     # Ядро приложения
│    │    ├── __init__.py
│    │    ├── currencies.py        # ABC Currency, FiatCurrency, CryptoCurrency
│    │    ├── exceptions.py        # Кастомные исключения
│    │    ├── models.py            # User, Wallet, Portfolio
│    │    ├── usecases.py          # Бизнес-логика (AppContext)
│    │    └── utils.py             # Вспомогательные функции
│    ├── infra/                    # Инфраструктура
│    │    ├── __init__.py
│    │    ├── settings.py          # Singleton SettingsLoader
│    │    └── database.py          # Singleton DatabaseManager
│    ├── parser_service/           # Сервис парсинга курсов
│    │    ├── __init__.py
│    │    ├── config.py            # Конфигурация API (env, списки валют)
│    │    ├── api_clients.py       # CoinGeckoClient, ExchangeRateApiClient
│    │    ├── storage.py           # Атомарная запись JSON
│    │    └── updater.py           # Координатор обновления курсов
│    └── cli/
│         ├── __init__.py
│         └── interface.py         # Консольный интерфейс (shlex)
│
├── logs/                          # Логи операций (игнорируется Git)
│    └── actions.log
│
├── main.py                        # Точка входа
├── pyproject.toml                 # Конфигурация uv и ruff
├── uv.lock                        # Зафиксированные зависимости
├── README.md                      # Документация проекта
├── demo_script.md                 # Сценарий демонстрации
└── .gitignore

## 🛠️ Установка и запуск

### Требования
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — современный менеджер пакетов

### Установка
```bash
# Клонировать репозиторий
git clone <your-repo-url>
cd finalproject_Shoshina_M26-555

# Установить зависимости (uv автоматически создаст .venv)
uv sync

## Запуск
```
uv run wallet
```

## 💻 Команды CLI

### Основные команды
| Команда | Описание |
|---------|----------|
| `register --username <name> --password <pass>` | Регистрация нового пользователя |
| `login --username <name> --password <pass>` | Вход в систему |
| `logout` | Выход из системы |
| `show-portfolio [--base <curr>]` | Показать портфель в виде таблицы |
| `buy --currency <curr> --amount <num>` | Купить валюту |
| `sell --currency <curr> --amount <num>` | Продать валюту (с подтверждением) |
| `get-rate --from <curr> --to <curr>` | Узнать курс валюты |

### Команды Parser Service
| Команда | Описание |
|---------|----------|
| `update-rates [--source <src>]` | Обновить курсы из внешних API (coingecko / exchangerate) |
| `show-rates [--currency <curr>] [--top <n>]` | Показать кэш курсов с фильтрацией |

---

## 📋 Примеры использования

### 1. Покупка и просмотр портфеля
```text
wallet> buy --currency BTC --amount 0.5
Покупка выполнена: 0.5000 BTC по курсу 59337.21 USD/BTC
Изменения в портфеле:
- BTC: было 0.0000 → стало 0.5000
Оценочная стоимость покупки: 29,668.60 USD

wallet> show-portfolio
Портфель пользователя 'alice' (база: USD):
+--------+-----------+------------+-----------------+
| Валюта |    Баланс | Курс к USD | Стоимость (USD) |
+--------+-----------+------------+-----------------+
| BTC    |    0.5000 | 59337.2100 |       29,668.60 |
| EUR    | 1000.0000 |     1.0786 |        1,078.60 |
| ИТОГО  |           |            |   30,747.20 USD |
+--------+-----------+------------+-----------------+
```
