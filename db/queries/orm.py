import datetime
import random
from typing import List

from sqlalchemy import Integer, and_, func, insert, select, text, update, delete
from sqlalchemy.orm import aliased
from db.database import sync_engine, session_factory, Base
from db.models import Deals, Coins, ListOfOpenDeals


class SyncCore:
    @staticmethod
    def create_tables():
        sync_engine.echo = True
        Base.metadata.drop_all(sync_engine)
        Base.metadata.create_all(sync_engine)
        with session_factory() as session:
            # Список монет
            coin_names = [
                "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT",
                "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT",
                "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT",
                "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"
            ]

            # Проверяем, есть ли уже данные в таблице
            if session.query(Coins).count() == 0:
                # Добавляем монеты в базу данных
                session.add_all([Coins(coin=coin) for coin in coin_names])
                session.commit()

        sync_engine.echo = True

class DealsOrm:
    @staticmethod
    def append_deal(coin, order_id_buy, order_id_sell, money_buy, tax_buy, money_sell, tax_sell, status):
        with session_factory() as session:
            # row = {
            #     "coin": spot.symbol,
            #     "side": spot.side_buy,
            #     "order_id_buy": spot.order_id_buy,
            #     "order_id_sell": spot.order_id_sell,
            #     "money_buy": round(float(spot.money_buy), 3),
            #     "tax_buy": round(float(spot.tax_buy), 3),
            #     "money_sell": round(float(spot.money_sell), 3), #'0.0',
            #     "tax_sell": round(float(spot.tax_sell), 3),
            #     "status": spot.status_buy,
            #     "time_sell": WorkWithCSV.make_str_date_from_timestamp(spot.time_buy),
            #     "time_close": 0,
            #     "time_in_deal": 0
            # }
            query = insert(Deals).values(coin=coin, order_id_buy=order_id_buy, order_id_sell=order_id_sell,
                                         money_buy=round(float(money_buy), 3), tax_buy=round(float(tax_buy), 3),
                                         money_sell=round(float(money_sell), 3), tax_sell=round(float(tax_sell), 3),
                                         status=status, time_in_deal=datetime.timedelta(seconds=0), earn=0) #time_open=time_sell, time_close=0,
            session.execute(query)
            session.commit()

    @staticmethod
    def find_deal_for_update(coin, status_sell):
        with session_factory() as session:
            query = select(Deals).filter_by(coin=coin, status=status_sell)
            res = session.execute(query)
            result = res.scalars().one()
            session.commit()
            return result #result.order_id_sell

    @staticmethod
    def update_deal(coin, status, money_sell, tax_sell):
        with session_factory() as session:
            query = select(Deals).filter_by(coin=coin, status="Filled")
            res = session.execute(query)
            deal_for_update = res.scalars().first() #.one()
            print(f"deal_for_update: {deal_for_update}")
            #deal_for_update = DealsOrm.find_deal_for_update(coin, "Filled")
            if not deal_for_update:
                print("Ошибка: Сделка не найдена!")
                return
            print(f"Найдена сделка: {deal_for_update}")
            deal_for_update.status = status
            deal_for_update.money_sell = round(float(money_sell), 3)
            deal_for_update.tax_sell = round(float(tax_sell), 3)
            deal_for_update.time_close = datetime.datetime.now()
            deal_for_update.time_in_deal = deal_for_update.time_close - deal_for_update.time_open
            deal_for_update.earn = deal_for_update.money_sell - deal_for_update.money_buy - deal_for_update.tax_buy - deal_for_update.tax_sell
            #session.add(deal_for_update)
            session.commit()

        #     # Данные для обновления
        #     data = {
        #         "coin": spot.symbol,
        #         "money_sell": round(float(spot.money_sell), 3),
        #         "tax_sell": round(float(spot.tax_sell), 3),
        #         "status": spot.earn,
        #         "time_close": WorkWithCSV.make_str_date_from_timestamp(spot.time_close),
        #         "time_in_deal": WorkWithCSV.count_time_in_deal(spot.time_sell, spot.time_close)
        #     }

class CoinsOrm:
    @staticmethod
    def select_coins():
        with session_factory() as session:
            query = select(Coins).filter_by(in_deal=False)
            res = session.execute(query)
            result = res.scalars().all()
            session.commit()
            print(f"RESS: {result}")
            for coin in result:
                print(f"ID: {coin.id}, Coin: {coin.coin}")

    @staticmethod
    def delete_coin(coin: str):
        with session_factory() as session:
            #query = delete(Coins).where(Coins.coin == coin)
            #delete_coin = Coins(coin=coin, in_deal=True)
            #query = update(Coins).values(in_deal=True).where(Coins.coin==coin)
            query = update(Coins).values(in_deal=True).filter_by(coin=coin)
            session.execute(query)
            session.commit()

    @staticmethod
    def add_coin(coin: str):
        with session_factory() as session:
            query = update(Coins).values(in_deal=False).filter_by(coin=coin)
            session.execute(query)
            session.commit()

class ListOfOpenDealsOrm:
    @staticmethod
    def select_all_deals() -> List[str]:
        with session_factory() as session:
            query = select(ListOfOpenDeals)
            res = session.execute(query)
            session.commit()
            result = res.scalars().all()
            list_of_deals = []
            for deal in result:
                list_of_deals.append(deal.order_id)
            return list_of_deals


    @staticmethod
    def append_deal(coin: str, order_id: str):
        with session_factory() as session:
            query = insert(ListOfOpenDeals).values(coin=coin, order_id=order_id)
            session.execute(query)
            session.commit()

    @staticmethod
    def delete_deal(order_id: str):
        with session_factory() as session:
            query = delete(ListOfOpenDeals).filter_by(order_id=order_id)
            session.execute(query)
            session.commit()

    # @staticmethod
    # def add_coin_random_place(coin: str):
    #     with session_factory() as session:  # Открываем сессию
    #         # Получаем все монеты
    #         existing_coins = session.scalars(select(Coins)).all()
    #
    #         # Если таблица пустая, просто добавляем монету
    #         if not existing_coins:
    #             session.add(Coins(coin=coin))
    #         else:
    #             # Выбираем случайную позицию
    #             random_index = random.randint(0, len(existing_coins))
    #
    #             # Разбиваем список и вставляем монету
    #             new_coins = existing_coins[:random_index] + [Coins(coin=coin)] + existing_coins[random_index:]
    #
    #             # Очищаем таблицу и записываем новый порядок
    #             session.execute(delete(Coins))  # Удаляем старые записи
    #             session.add_all(new_coins)  # Добавляем обновленный список
    #
    #         session.commit()  # Сохраняем изменения

    # @staticmethod
    # def create_coins_table():
    #     Base.metadata.create_all(sync_engine)
    #     with session_factory() as session:
    #         # Список монет
    #         coin_names = [
    #             "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT",
    #             "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT",
    #             "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT",
    #             "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"
    #         ]
    #
    #         # Проверяем, есть ли уже данные в таблице
    #         if session.query(Coins).count() == 0:
    #             # Добавляем монеты в базу данных
    #             session.add_all([Coins(coin=coin) for coin in coin_names])
    #             session.commit()

    # @staticmethod
    # def create_list_of_deals_table():
    #     Base.metadata.create_all(sync_engine)
    #     with session_factory() as session:
    #         session.commit()

    #
    # @staticmethod
    # def insert_data():
    #     with sync_engine.connect() as conn:
    #         stmt = insert(Deals).values(
    #             [
    #                 {"coin": "BTCUSDT", "order_id_buy": "3252526", "order_id_sell": "23213"},
    #                 {"coin": "ETHUSDT", "order_id_buy": "222222", "order_id_sell": "1111"}
    #             ]
    #         )
    #         conn.execute(stmt)
    #         conn.commit()
    #
    # @staticmethod
    # def insert_workers():
    #     with session_factory() as session:
    #         deal_1 = Deals(coin="BTCUSDT", order_id_buy="3252526", order_id_sell="23213")
    #         deal_2 = Deals(coin="ETHUSDT", order_id_buy="11111", order_id_sell="45")
    #         session.add_all([deal_1, deal_2])
    #         # flush отправляет запрос в базу данных
    #         # После flush каждый из работников получает первичный ключ id, который отдала БД
    #         session.flush()
    #         session.commit()