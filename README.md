# ValutaTrade Hub — Консольный валютный кошелёк

## Описание проекта

**ValutaTrade Hub** — консольное приложение для управления виртуальным портфелем фиатных и криптовалют. Пользователи могут регистрироваться, совершать сделки по покупке/продаже, отслеживать актуальные курсы в реальном времени через интеграцию с внешними API (CoinGecko, ExchangeRate-API).

### Ключевые возможности

- Регистрация и безопасный вход (SHA-256 с солью)
- Управление портфелем: покупка/продажа валют с оценкой стоимости
- Отслеживание курсов через **CoinGecko** (крипто) и **ExchangeRate-API** (фиат)
- Вывод данных в виде таблиц (`prettytable`)
- Логирование всех операций с ротацией файлов
- Подтверждение критичных действий (продажа)
- Кэширование курсов (TTL) для экономии запросов к API

---

## Архитектура проекта

```text
finalproject_Shoshina_M26-555/
│
├── data/                          # Хранилище данных (не коммитится, см. .gitignore)
│    ├── users.json                # Пользователи (хеши паролей + соль)
│    ├── portfolios.json           # Портфели и кошельки
│    ├── rates.json                # Актуальные курсы (кэш для Core)
│    └── exchange_rates.json       # История курсов (Parser Service)
│
├── src/finalproject_shoshina_m26_555/
│    ├── __init__.py
│    ├── exceptions.py             # Кастомные исключения (корень пакета)
│    ├── core/                     # Ядро приложения
│    │    ├── __init__.py
│    │    ├── currencies.py        # ABC Currency, FiatCurrency, CryptoCurrency, фабрика
│    │    ├── decorators.py        # @log_action, @confirm_action, @rate_cache
│    │    ├── logging_config.py    # Настройка логирования с ротацией
│    │    ├── models.py            # User, Wallet, Portfolio
│    │    ├── usecases.py          # Бизнес-логика (AppContext)
│    │    └── utils.py             # hash_password, generate_salt
│    ├── infra/                    # Инфраструктура
│    │    ├── __init__.py
│    │    ├── settings.py          # Singleton SettingsLoader
│    │    └── database.py          # Singleton DatabaseManager (атомарная запись)
│    ├── parser_service/           # Сервис парсинга курсов
│    │    ├── __init__.py
│    │    ├── config.py            # Конфигурация API (env, списки валют)
│    │    ├── api_clients.py       # CoinGeckoClient, ExchangeRateApiClient
│    │    ├── storage.py           # Атомарная запись rates.json + история
│    │    └── updater.py           # Координатор обновления курсов
│    └── cli/
│         ├── __init__.py
│         └── interface.py         # Консольный интерфейс (shlex)
│
├── logs/                          # Логи операций (не коммитится)
│    └── actions.log
│
├── pyproject.toml                 # Конфигурация uv и ruff
├── uv.lock                        # Зафиксированные зависимости
├── README.md                      # Документация проекта
└── .gitignore
```

---

## Установка и запуск

### Требования

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — менеджер пакетов

### Установка

```bash
git clone https://github.com/EAShoshina/finalproject_Shoshina_M26-555.git
cd finalproject_Shoshina_M26-555
uv sync
```

### Запуск

```bash
uv run wallet
```

---

## Команды CLI

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
| `help` | Список команд |
| `exit` / `quit` | Выход |

### Команды Parser Service

| Команда | Описание |
|---------|----------|
| `update-rates [--source coingecko\|exchangerate]` | Обновить курсы из внешних API |
| `show-rates [--currency <curr>] [--top <n>]` | Показать кэш курсов с фильтрацией |

---

## Примеры использования

### 1. Регистрация, вход, покупка, портфель

```text
wallet> register --username alice --password 1234
Пользователь 'alice' зарегистрирован (id=1). Войдите: login --username alice --password ****

wallet> login --username alice --password 1234
Вы вошли как 'alice'

wallet> buy --currency BTC --amount 0.5
Покупка выполнена: 0.5000 BTC по курсу 76061.00 USD/BTC
Изменения в портфеле:
- BTC: было 0.0000 → стало 0.5000
Оценочная стоимость покупки: 38,030.50 USD

wallet> show-portfolio
Портфель пользователя 'alice' (база: USD):
+--------+-----------+------------+-----------------+
| Валюта |    Баланс | Курс к USD | Стоимость (USD) |
+--------+-----------+------------+-----------------+
| BTC    |    0.5000 | 76061.0000 |       38,030.50 |
| ИТОГО  |           |            |   38,030.50 USD |
+--------+-----------+------------+-----------------+
```

### 2. Продажа с подтверждением и обработка ошибок

```text
wallet> sell --currency BTC --amount 5.0

Вы уверены, что хотите продать эту валюту? [y/N]: y
Ошибка: Недостаточно средств: доступно 0.5000 BTC, требуется 5.0000 BTC
```

```text
wallet> buy --currency DOGE --amount 100
Ошибка: Неизвестная валюта 'DOGE'
```

### 3. Работа с курсами (Parser Service)

```text
wallet> update-rates --source coingecko
Update successful. Total rates updated: 3.

wallet> show-rates --top 2
Rates from cache (last refresh: 2026-11-06T12:01:27):
+---------+--------------+---------------------+-----------+
| Пара    |         Курс |           Обновлено |  Источник |
+---------+--------------+---------------------+-----------+
| BTC_USD | 76051.000000 | 2026-11-06T12:01:27 | CoinGecko |
| ETH_USD |  2240.480000 | 2026-11-06T12:01:27 | CoinGecko |
+---------+--------------+---------------------+-----------+

wallet> get-rate --from BTC --to USD
Курс BTC→USD: 76051.00000000 (обновлено: 2026-11-06T12:01:27Z)
Обратный курс USD→BTC: 0.00001315
```

**Без `EXCHANGERATE_API_KEY`** `update-rates` без `--source` вернёт `Update completed with errors` + `403` (демо-ключ), но `rates.json` обновится крипто-парами (3). Для фиата задайте ключ (см. ниже).

---

## Продвинутые возможности (Архитектура)

- **Паттерны проектирования**:
  - **Singleton**: `SettingsLoader` (конфигурация), `DatabaseManager` (JSON через `__new__`).
  - **Factory**: `get_currency()` — фабрика валют с реестром.
  - **ABC**: `Currency` → `FiatCurrency`, `CryptoCurrency`.
  - **Decorator**: `@log_action`, `@confirm_action`, `@rate_cache`.
- **Логирование**: `logs/actions.log` с ротацией (5 МБ, 3 бэкапа), формат `LEVEL ISO8601 message`, поля `user=`, `currency=`, `amount=`, `result=`.
- **Безопасность**: `hashlib.sha256(password + salt)`, безопасный парсинг CLI через `shlex`.
- **Отказоустойчивость API**: падение одного клиента не стопорит обновление; ошибки логируются, `run_update` возвращает `success=False` + `errors`.
- **Атомарная запись**: `rates.json`, `exchange_rates.json`, `users.json`, `portfolios.json` пишутся через tmp → replace.
- **Кэширование**: `@rate_cache(ttl_seconds=settings.rates_ttl_seconds)` (по умолчанию 300 с).
- **TTL**: `rates.json` хранит `updated_at` и `last_refresh`; `get-rate` показывает дату обновления.

---

## Настройка API-ключей

Для фиатных курсов получите бесплатный ключ на [exchangerate-api.com](https://www.exchangerate-api.com/) и задайте переменную окружения:

#### Windows (PowerShell)

```powershell
$env:EXCHANGERATE_API_KEY="ваш_ключ_здесь"
uv run wallet
```

#### Linux / macOS

```bash
export EXCHANGERATE_API_KEY="ваш_ключ_здесь"
uv run wallet
```

Без ключа приложение работает в демо-режиме: обновляются только крипто-курсы (CoinGecko), для фиата используется `fallback_rates` из `infra/settings.py`.

---

## Разработка

```bash
# Линтер
uv run ruff check src/

# Авто-исправление
uv run ruff check src/ --fix
```

---

## Хранение данных

Файлы `data/users.json`, `data/portfolios.json`, `data/rates.json`, `data/exchange_rates.json` **не коммитятся** (см. `.gitignore`) — они создаются при первом запуске и содержат пользовательские данные / кэш курсов.