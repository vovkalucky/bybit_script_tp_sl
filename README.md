# Bybit Trade Script
Краткое описание проекта: 
Python скрипт осуществляет автоматическую торговлю по заданному алгоритму, используя API биржи Bybit. 
Каждый ордер записывается в таблицу deals, список доступных монет для торговли в таблице coins.
Логирование настроено через Docker контейнер и ведется в script_logs
Pipeline для автоматизации деплоя на VPS описан в .github/workflows/deploy.yml

Вся инфраструктура проекта развернута в трех Docker контейнерах и запущена на VPS iPhoster.net: 
1. bybit_tp_sl (основной python скрипт с торговым алгоритмом)
2. postgres_db (база данных с двумя таблицами deals и coins)
3. pgadmin (админ панель для работы с БД) http://addres_server:5050/

При push изменении в репозиторий github через Github Actions:
1. Запускается прогон автотестов
2. Формируется allure отчет с результатом прохождения автотестов
3. При успешном прохождении всех автотестов деплой проекта на VPS.

## 📌 Функции
🚀 Основные возможности проекта:
Автоматический поиск точек для входа в сделку, установка торговых ордеров на вход/выход в сделку
⚡️ Ключевые особенности
Поиск точки входа по неограниченному количеству монет. Текущий список торговых пар:
["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", 
"APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT", 
"ONDOUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]
Отправка сообщений в Telegram бот при успешном деплое проекта, открытии/закрытии сделки.
- 🔧 Дополнительные настройки в файле settings.py

## 🛠️ Инструменты
Python (pybit, tradingview-ta, pytest, allure, sqlalchemy)
PostgresDB (pgadmin)
Docker (docker compose)
Telegram API

## 🗣 Основные команды
Поднимаем БД и pgadmin (docker-compose-DB.yml):
docker compose up -d

Запуск скрипта (docker-compose.yml):
docker compose up -d
docker compose down
docker logs -f bybit_tp_sl

Тесты:
pytest -s -v
pytest -s -v --alluredir=allure_results


