import datetime
from typing import List
from sqlalchemy import insert, select, update
import config
from classes.OrdersStructure import Order
from db.database import session_factory, Base, get_engine
from db.models import Deals, Coins


class BaseOrm:
    @staticmethod
    def create_tables():
        try:
            sync_engine = get_engine()
            sync_engine.echo = True
            #assert config.MODE == "TEST"
            #Base.metadata.drop_all(sync_engine)
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

            sync_engine.echo = False
            print("✅ Таблицы coins, deals успешно созданы")
        except Exception as e:
            print(f"[create_tables] Не удалось создать таблицы: {e}")


class DealsOrm:
    @staticmethod
    # def append_deal(coin: str, order_id_open: str, order_id_close: str, money_open: str,
    #                 tax_open: str, money_close: str, tax_close: str, status: str):
    def append_deal(order: Order):
        try:
            with session_factory() as session:
                query = insert(Deals).values(coin=order.symbol, order_id_open=order.order_id, order_id_close=order.order_id_close,
                                             money_open=round(float(order.money_open), 3), tax_open=round(float(order.tax_open), 3),
                                             money_close=order.money_close, tax_close=order.tax_close,
                                             status=order.status, time_in_deal=datetime.timedelta(seconds=0), earn=0) #time_open=time_sell, time_close=0,

                session.execute(query)
                session.commit()
                print("➕ Данные о сделке добавлены в таблицу deals")
        except Exception as e:
            print(f"[append_deal] {e}")

    @staticmethod
    def update_deal(order: Order):
        try:
            with session_factory() as session:
                deal = session.query(Deals).filter(
                    Deals.coin == order.symbol,
                    Deals.status.notin_(["Filled", "Deactivated"])
                ).first()

                if not deal:
                    print("[update_deal] Ошибка: Сделка для обновления не найдена!")
                    return

                # Вычисления на основе найденной сделки
                now = datetime.datetime.now()
                time_in_deal = now - deal.time_open
                money_close = round(float(order.money_close), 3)
                tax_close = round(float(order.tax_close), 3)

                if order.status != "Deactivated":
                    if order.status == "Buy":
                        earn = round(
                            money_close - deal.money_open - deal.tax_open - tax_close, 3
                        )
                    elif order.status == "Sell":
                        earn = round(
                            deal.money_open - money_close - deal.tax_open - tax_close, 3
                        )
                if order.status == "Deactivated":
                    earn = 0
                print(f"[update_deal] {earn}")
                # Обновляем значения
                deal.status = order.status
                deal.money_close = money_close
                deal.tax_close = tax_close
                deal.time_close = now
                deal.time_in_deal = time_in_deal
                deal.earn = earn

                session.commit()
                print("♻️ Сделка обновлена в таблице deals.")
        except Exception as e:
            print(f"[update_deal] Ошибка: {e}")

    @staticmethod
    def get_earn(order_id_sell: str):
        with (session_factory() as session):
            query = select(Deals).filter(Deals.order_id_close == order_id_sell)
            res = session.execute(query)
            deal_for_update = res.scalars().first()
            session.commit()
            return deal_for_update.earn

    @staticmethod
    def select_open_deals():
        with (session_factory() as session):
            query = select(Deals.order_id_close).filter(
                Deals.status.notin_(["Filled", "Deactivated"])
            ).order_by(Deals.id)
            res = session.execute(query)
            list_of_deals = res.scalars().all()
            print(f"📄 Список открытых ордеров {list_of_deals}")
            return list_of_deals


class CoinsOrm:
    @staticmethod
    def select_coins() -> List[str]:
        with session_factory() as session:
            query = select(Coins).filter_by(in_deal=False).order_by(Coins.id)
            res = session.execute(query)
            result = res.scalars().all()
            coins = []
            for coin in result:
                coins.append(coin.coin)
            return coins

    @staticmethod
    def delete_coin(coin: str):
        with session_factory() as session:
            query = update(Coins).values(in_deal=True).filter_by(coin=coin)
            session.execute(query)
            session.commit()

    @staticmethod
    def add_coin(coin: str):
        with session_factory() as session:
            query = update(Coins).values(in_deal=False).filter_by(coin=coin)
            session.execute(query)
            session.commit()