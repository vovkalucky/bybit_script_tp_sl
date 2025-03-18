# Bybit Trade Script
Краткое описание проекта: автоматическая торговля через API биржи Bybit по заданному торговому алгоритму. 
Каждый ордер записывается в таблицу deals (Postgres DB)
Логирование настроено через Docker контейнер и ведется в script_logs
Pipeline для автоматизации деплоя на VPS описан в .github/workflows/


## 📌 Функции
🚀 Основные возможности проекта:
Автоматический поиск точек для входа в сделку, установка торгового ордера
⚡️ Ключевые особенности
Поиск точки входа по неограниченному количеству монет. Текущий список торговых пар:
["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", 
"APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT", 
"HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]
При push изменении в репозиторий github через Github Actions запускается прогон автотестов и деплой проекта на VPS.
Отправка сообщений в Telegram бот при успешном деплое проекта, открытии/закрытии сделки.

- 🔧 Дополнительные настройки в файле settings.py

## 🛠️ Инструменты
Python (pybit, tradingview-ta, pytest, allure, sqlalchemy)
PostgresDB (pgadmin)
Docker (docker compose)
Telegram API

Вся инфраструктура проекта развернута в трех Docker контейнерах и запущена на VPS iPhoster.net: 
1. bybit_tp_sl (основной python скрипт с торговым алгоритмом)
2. postgres_db (база данных с двумя таблицами deals и coins)
3. pgadmin (админка для работы с таблицами) http://addres_server:5050/


## 🗣 Основные команды
Запуск:
docker compose up -d
docker compose down
docker logs -f bybit_tp_sl

Тесты:
pytest -s -v


