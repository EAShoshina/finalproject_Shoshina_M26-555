uv run python -c "
content = '''# ValutaTrade Hub — Консольный валютный кошелёк

## 📖 Описание проекта

**ValutaTrade Hub** — это консольное приложение для управления виртуальным портфелем фиатных и криптовалют. Пользователи могут регистрироваться, совершать сделки по покупке/продаже, отслеживать актуальные курсы в реальном времени через интеграцию с внешними API.

### Ключевые возможности:
- 🔐 Регистрация и безопасный вход (хеширование паролей с солью через SHA-256)
- 💼 Управление портфелем: покупка/продажа валют с оценкой стоимости
- 📈 Отслеживание курсов через **CoinGecko** (крипто) и **ExchangeRate-API** (фиат)
- 📊 Красивый вывод данных в виде таблиц (\`prettytable\`)
- 📝 Логирование всех операций с ротацией файлов
- ✅ Подтверждение критичных действий (продажа)
- ⚡ Кэширование курсов (TTL) для экономии запросов к API

---

## 🏗️ Архитектура проекта

\`\`\`text
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
\`\`\`

---

## 🛠️ Установка и запуск

### Требования
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — современный менеджер пакетов

### Установка
\`\`\`bash
git clone https://github.com/EAShoshina/finalproject_Shoshina_M26-555.git
cd finalproject_Shoshina_M26-555
uv sync
\`\`\`

### Запуск
\`\`\`bash
uv run wallet
\`\`\`

---

## 💻 Команды CLI

### Основные команды
| Команда | Описание |
|---------|----------|
| \`register --username <name> --password <pass>\` | Регистрация нового пользователя |
| \`login --username <name> --password <pass>\` | Вход в систему |
| \`logout\` | Выход из системы |
| \`show-portfolio [--base <curr>]\` | Показать портфель в виде таблицы |
| \`buy --currency <curr> --amount <num>\` | Купить валюту |
| \`sell --currency <curr> --amount <num>\` | Продать валюту (с подтверждением) |
| \`get-rate --from <curr> --to <curr>\` | Узнать курс валюты |

### Команды Parser Service
| Команда | Описание |
|---------|----------|
| \`update-rates [--source <src>]\` | Обновить курсы из внешних API |
| \`show-rates [--currency <curr>] [--top <n>]\` | Показать кэш курсов с фильтрацией |

---

## 📋 Примеры использования

### 1. Покупка и просмотр портфеля
\`\`\`text
wallet> buy --currency BTC --amount 0.5
Покупка выполнена: 0.5000 BTC по курсу 59337.21 USD/BTC
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
\`\`\`

### 2. Продажа с подтверждением и обработка ошибок
\`\`\`text
wallet> sell --currency BTC --amount 5.0
Вы уверены, что хотите продать эту валюту? [y/N]: y
Ошибка: Недостаточно средств: доступно 0.5000 BTC, требуется 5.0000 BTC

wallet> buy --currency DOGE --amount 100
Ошибка: Неизвестная валюта 'DOGE'
\`\`\`

### 3. Работа с курсами (Parser Service)
\`\`\`text
wallet> update-rates
Update successful. Total rates updated: 6.

wallet> show-rates --top 2
Rates from cache (last refresh: 2026-11-04T16:27:41):
+---------+--------------+---------------------+-----------+
| Пара    |         Курс |           Обновлено |  Источник |
+---------+--------------+---------------------+-----------+
| BTC_USD | 80445.000000 | 2026-11-04T16:27:41 | CoinGecko |
| ETH_USD |  2430.140000 | 2026-11-04T16:27:41 | CoinGecko |
+---------+--------------+---------------------+-----------+
\`\`\`

---

## 🔧 Продвинутые возможности (Архитектура)

- 🏛️ **Паттерны проектирования**: Singleton (\`SettingsLoader\`, \`DatabaseManager\`), Factory (\`get_currency\`), ABC (\`Currency\`), Decorator (\`@log_action\`, \`@confirm_action\`, \`@rate_cache\`).
- 📝 **Логирование**: Все операции логируются в \`logs/actions.log\` с ротацией (5 МБ, 3 бэкапа) через \`RotatingFileHandler\`.
- 🔐 **Безопасность**: Пароли хешируются через \`hashlib.sha256(password + salt)\`. Безопасный парсинг CLI через \`shlex\`.
- 🌐 **Отказоустойчивость API**: Если один API возвращает ошибку (403/429), \`RatesUpdater\` перехватывает исключение и продолжает работу со вторым источником.
- ⚡ **Кэширование**: Курсы кэшируются в \`data/rates.json\` с настраиваемым TTL через замыкание \`@rate_cache\`.

---

## 🔑 Настройка API-ключей

Для полноценной работы получите бесплатный ключ на [exchangerate-api.com](https://www.exchangerate-api.com/) и установите переменную окружения:

**Windows (PowerShell):**
\`\`\`powershell
\$env:EXCHANGERATE_API_KEY=\"ваш_ключ_здесь\"
uv run wallet
\`\`\`

**Linux / macOS:**
\`\`\`bash
export EXCHANGERATE_API_KEY=\"ваш_ключ_здесь\"
uv run wallet
\`\`\`
*Без ключа приложение использует демо-режим с ограничениями.*
'''
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(content)
print('✅ Файл README.md успешно создан!')
"