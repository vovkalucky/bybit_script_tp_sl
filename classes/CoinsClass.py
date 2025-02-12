import json
import random
from settings import COINS_LIST


class CoinsClass:

    #coins = CoinsClass.load_coins()
    # coins = load_coins()

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

    # def get_coins(self):
    #     """Возвращает текущий список COINS."""
    #     return self.coins

# class CoinsClass:
#     def __init__(self):
#         self.coins = self.load_coins()
#     #coins = load_coins()
#
#
#     @staticmethod
#     def load_coins():
#         """Загружает список COINS из файла, если файл существует."""
#         try:
#             with open(COINS_LIST, "r") as f:
#                 return json.load(f)
#         except (FileNotFoundError, json.JSONDecodeError):
#             print(f"Файл {COINS_LIST} не найден!")
#             # Если файл не существует или поврежден, возвращаем исходный список
# #             return [
# #     "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
# #     "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT",
# #     "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT",
# #     "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT"
# # ]
#
#     def save_coins(self):
#         """Сохраняет текущий список COINS в файл."""
#         with open(COINS_LIST, "w") as f:
#             json.dump(self.coins, f) #indent=4
#
#     def remove_coin(self, coin_name):
#         """Удаляет торговую пару из списка COINS."""
#         if coin_name in self.coins:
#             self.coins.remove(coin_name)
#             self.save_coins()
#         else:
#             print(f"{coin_name} не найдена в списке.")
#
#     def add_coin(self, coin_name):
#         """Добавляет торговую пару в случайное место списка COINS и она снова становится доступной для торговли"""
#         if coin_name not in self.coins:
#             # Генерация случайного индекса
#             random_index = random.randint(0, len(self.coins))
#             # Добавление элемента в случайное место
#             self.coins.insert(random_index, coin_name)
#             self.save_coins()
#         else:
#             print(f"{coin_name} уже есть в списке.")
#
#     def get_coins(self):
#         """Возвращает текущий список COINS."""
#         return self.coins
