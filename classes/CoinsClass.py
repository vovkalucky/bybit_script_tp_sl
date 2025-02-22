import json
import random
from settings import COINS_LIST


class CoinsClass:
    @staticmethod
    def load_coins():
        """Загружает список COINS из файла, если файл существует."""
        try:
            with open(COINS_LIST, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Файл {COINS_LIST} не найден!")

    @staticmethod
    def save_coins(coins):
        """Сохраняет текущий список COINS в файл."""
        with open(COINS_LIST, "w") as f:
            json.dump(coins, f)  # indent=4

    @staticmethod
    def remove_coin(coins, coin_name):
        """Удаляет торговую пару из списка COINS."""
        if coin_name in coins:
            coins.remove(coin_name)
            CoinsClass.save_coins(coins)
        else:
            print(f"{coin_name} не найдена в списке.")

    @staticmethod
    def add_coin(coins, coin_name):
        """Добавляет торговую пару в случайное место списка COINS и она снова становится доступной для торговли"""
        if coin_name not in coins:
            # Генерация случайного индекса
            random_index = random.randint(0, len(coins))
            # Добавление элемента в случайное место
            coins.insert(random_index, coin_name)
            CoinsClass.save_coins(coins)
        else:
            print(f"{coin_name} уже есть в списке.")
