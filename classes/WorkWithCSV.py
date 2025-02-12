import json
import os
import csv
from settings import STATE_FILE, CSV_FILE
from datetime import datetime, timedelta

headers = ["coin", "side", "order_id_buy", "order_id_sell", "money_buy",
           "tax_buy", "money_sell", "tax_sell", "status", "time_sell", "time_close", "time_in_deal"]

class WorkWithCSV:
    @staticmethod
    def load_deals():
        """Загружает сделки из файла."""
        try:
            with open(STATE_FILE, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return {"list_of_deals": []}
        except json.JSONDecodeError:
            return {"list_of_deals": []}

    @staticmethod
    def save_deals(order):
        """Сохраняет сделку в файл."""
        with open(STATE_FILE, "w") as file:
            json.dump(order, file)

    @staticmethod
    def append_order_to_csv(spot):
        try:
            # headers = ["coin", "side", "order_id_buy", "order_id_sell", "money_buy",
            #            "tax_buy", "money_sell", "tax_sell", "status"]
            file_exists = os.path.exists(CSV_FILE)
            # Формируем строку для записи

            row = {
                "coin": spot.symbol,
                "side": spot.side_buy,
                "order_id_buy": spot.order_id_buy,
                "order_id_sell": spot.order_id_sell,
                "money_buy": round(float(spot.money_buy), 3),
                "tax_buy": round(float(spot.tax_buy), 3),
                "money_sell": round(float(spot.money_sell), 3), #'0.0',
                "tax_sell": round(float(spot.tax_sell), 3),
                "status": spot.status_buy,
                "time_sell": WorkWithCSV.make_str_date_from_timestamp(spot.time_buy),
                "time_close": 0,
                "time_in_deal": 0
            }
            # Проверяем корректность данных для записи
            if not isinstance(row, dict):
                raise ValueError("❗️Формат строки для записи должен быть словарём.")
            # Открываем файл для добавления данных
            with open(CSV_FILE, "a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                # Если файл создаётся впервые, пишем заголовки
                if not file_exists:
                    writer.writeheader()
                # Записываем строку
                writer.writerow(row)
            print("➕ Данные о сделке добавлены в таблицу money.csv")
        except Exception as e:
            print(f"❗️Ошибка при добавлении данных: {e}")

    @staticmethod
    def update_order_to_csv(spot):
        try:
            # Определяем заголовки
            # headers = ["coin", "side", "order_id_buy", "order_id_sell", "money_buy",
            #            "tax_buy", "money_sell", "tax_sell", "status"]
            if spot.status_sell == "Deactivated":
                spot.earn = 0.0
            else:
                spot.earn = WorkWithCSV.get_deal_from_csv(spot, "Filled")
            # Данные для обновления
            data = {
                "coin": spot.symbol,
                "money_sell": round(float(spot.money_sell), 3),
                "tax_sell": round(float(spot.tax_sell), 3),
                "status": spot.earn,
                "time_close": WorkWithCSV.make_str_date_from_timestamp(spot.time_close),
                "time_in_deal": WorkWithCSV.count_time_in_deal(spot.time_sell, spot.time_close)
            }

            # Проверка корректности данных
            if not isinstance(data, dict):
                raise ValueError("❗️Формат строки для записи должен быть словарём.")

            # Проверяем, существует ли файл
            file_exists = os.path.exists(CSV_FILE)
            rows = []  # Список для хранения данных файла
            updated = False  # Флаг обновления строки

            if file_exists:
                # Читаем существующие строки
                with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
                    reader = csv.DictReader(file)
                    rows = list(reader)

                # Ищем строку для обновления
                for row in rows:
                    if (
                            row.get('coin') == data['coin']
                            and row.get('money_sell') == '0.0'
                            and row.get('tax_sell') == '0.0'
                            and row.get('status') == 'Filled'
                    ):
                        # Обновляем только указанные ключи
                        for key, value in data.items():
                            if key in row:  # Только если ключ существует
                                row[key] = str(value)  # Преобразуем в строку
                        updated = True
                        break

            # Если строка не найдена, добавляем новую
            if not updated:
                rows.append({key: str(data.get(key, "")) for key in headers})

            # Перезаписываем файл
            with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()  # Записываем заголовки
                writer.writerows(rows)  # Записываем все строки
            print("♻️ Данные успешно обновлены в таблице.")

        except Exception as e:
            print(f"❗️Ошибка при обновлении данных: {e}")

    @staticmethod
    def get_deal_from_csv(spot, status: str) -> float:
        earn = 0.0
        # Проверяем, существует ли файл
        if not os.path.exists(CSV_FILE):
            print(f"⚠️ Файл {CSV_FILE} не найден.")
            return 0.0

        # Читаем данные из CSV
        try:
            with open(CSV_FILE, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if not reader.fieldnames:
                    print(f"⚠️ Файл {CSV_FILE} пуст или повреждён.")
                    return 0.0
                for row in reader:
                    if row.get('coin') == spot.symbol and row.get('status') == status:
                        try:
                            earn = round(
                                float(spot.money_sell) -
                                float(row.get('money_buy', 0)) -
                                float(row.get('tax_buy', 0)) -
                                float(spot.tax_sell), 3
                            )
                            # print(
                            #     f"DEBUG: money_sell={spot.money_sell} money_buy={row.get('money_buy')} tax_buy={row.get('tax_buy')} tax_sell={spot.tax_sell}")
                        except ValueError:
                            print(f"⚠️ Ошибка при расчёте прибыли для {spot.symbol}.")
                            return 0.0
        except Exception as e:
            print(f"❗️ Ошибка при чтении файла {CSV_FILE}: {e}")
            return 0.0
        return earn

    @staticmethod
    def make_str_date_from_timestamp(timestamp_ms: int) -> str:
        timestamp = int(timestamp_ms) // 1000
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def count_time_in_deal(time_sell: str, time_close: str) -> str:
        # Переводим строковые значения времени в целые числа
        time_sell = int(time_sell)
        time_close = int(time_close)
        # Вычисляем разницу во времени (в миллисекундах)
        time_in_deal_ms = time_close - time_sell
        # Переводим миллисекунды в секунды и отбрасываем дробную часть
        time_in_deal_sec = time_in_deal_ms // 1000  # Целочисленное деление
        # Преобразуем разницу во времени в объект timedelta
        delta = timedelta(seconds=time_in_deal_sec)
        # Форматируем разницу как часы, минуты, секунды
        formatted_time = str(delta)
        return formatted_time
