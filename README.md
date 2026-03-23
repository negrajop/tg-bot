# Telegram Mood Tracker

Простой проект для отслеживания настроения через Telegram-бота с хранением данных в SQLite, выдачей через FastAPI и построением графика.

## Что умеет проект

- принимать оценки настроения через Telegram-бота
- сохранять записи в SQLite
- отдавать историю через HTTP API
- строить график по сохранённым данным
- заполнять базу фейковыми данными для тестов

## Стек

- Python
- aiogram 3
- SQLite
- FastAPI
- requests
- matplotlib
- python-dotenv

## Структура

- `bot.py` — Telegram-бот
- `server.py` — API на FastAPI
- `client.py` — построение графика
- `db.py` — работа с SQLite
- `seed_fake_data.py` — генерация тестовых данных

## Подготовка

1. Создай виртуальное окружение и установи зависимости:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

2. Создай файл `.env` на основе `.env.example`.

Пример содержимого:

```env
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuVWxyZ
DB_PATH=database.db
API_URL=http://127.0.0.1:8000
```

## Запуск

Для полной работы проекта обычно нужны два отдельных терминала.

### 1. Запуск API

```powershell
.\.venv\Scripts\python.exe -m uvicorn server:app --reload
```

После запуска API будет доступен по адресу `http://127.0.0.1:8000`.

### 2. Запуск бота

```powershell
.\.venv\Scripts\python.exe bot.py
```

После этого бот начнёт принимать команды в Telegram и сохранять оценки настроения в базу.

### 3. Построение графика

```powershell
.\.venv\Scripts\python.exe client.py
```

Скрипт построит график и сохранит файл `mood_chart.png`.

## Заполнение базы тестовыми данными

Скрипт `seed_fake_data.py` добавляет фейковые записи за период с `2026-03-01` по текущую дату системы.

Запуск:

```powershell
.\.venv\Scripts\python.exe seed_fake_data.py
```

Если нужно сначала очистить существующие записи в этом диапазоне:

```powershell
.\.venv\Scripts\python.exe seed_fake_data.py --reset
```

## Пример сценария работы

1. Запусти API.
2. Запусти бота.
3. Отправь `/start` боту в Telegram и выбери настроение.
4. При необходимости заполни БД тестовыми данными через `seed_fake_data.py`.
5. Запусти `client.py`, чтобы построить график.

## Примечания

- Не запускай несколько экземпляров `bot.py` одновременно с одним и тем же токеном.
- База данных по умолчанию создаётся в файле `database.db`.
- Все компоненты проекта работают локально.
