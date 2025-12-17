import datetime
from typing import List
from sqlalchemy import insert, select, update, text, inspect
from settings import COINS, TABLE_DEALS, TABLE_COINS
from classes.OrdersStructure import Order
from db.database import session_factory, Base, get_engine
from db.models import Deals, Coins


class BaseOrm:
    @staticmethod
    def create_tables():
        try:
            engine = get_engine()
            engine.echo = True
            inspector = inspect(engine)

            # Получаем все таблицы в базе
            existing_tables = inspector.get_table_names()
            print(f"📋 Существующие таблицы: {existing_tables}")
            metadata = Base.metadata

            # Удаляем только указанные таблицы, если они существуют
            for table_name in [TABLE_DEALS, TABLE_COINS]:
                if table_name in existing_tables:
                    print(f"🗑️ Удаляем таблицу: {table_name}")
                    with engine.begin() as conn:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
                        conn.commit()
                        print(f"✅ Таблица {table_name} удалена")
                else:
                    print(f"⚠️ Таблица {table_name} не найдена в базе")

            # Создаём только нужные таблицы из модели (если они описаны в Base)
            metadata.create_all(engine, tables=[
                t for t in metadata.tables.values()
                if t.name in [TABLE_DEALS, TABLE_COINS]
            ])


            with session_factory() as session:
                # Проверяем, есть ли уже данные в таблице
                if session.query(Coins).count() == 0:
                    # Добавляем монеты в базу данных
                    session.add_all([Coins(coin=coin) for coin in COINS])
                    session.commit()

            engine.echo = False
            print(f"[create_tables] ✅ Таблицы {TABLE_COINS}, {TABLE_DEALS} успешно созданы")
        except Exception as e:
            print(f"[create_tables] Не удалось создать таблицы: {e}")


class DealsOrm:
    @staticmethod
    def append_deal(order: Order):
        try:
            with session_factory() as session:
                query = insert(Deals).values(coin=order.symbol, order_id_open=order.order_id, side_open=order.side_open, qty_open=order.qty_open,
                                             money_open=round(float(order.money_open), 3), tax_open=round(float(order.tax_open), 3),
                                             order_id_close=order.order_id_close,
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
                money_close = round(float(order.money_close), 4)
                print(f"[update_deal] {order}")
                tax_close = round(float(order.tax_close), 4)


                earn = 0
                print(f"[update_deal] money {deal.money_open} {deal.tax_open} {money_close} {tax_close}")
                print(f"[update_deal] qty_open qty_close order.price: {deal.qty_open} {order.qty_close} {order.price}")
                if order.status != "Deactivated":
                    earn = round(money_close - deal.money_open - deal.tax_open - tax_close, 4)
                deal.status = order.status
                deal.money_close = money_close
                deal.tax_close = tax_close
                deal.time_close = now
                deal.time_in_deal = time_in_deal
                deal.earn = earn
                deal.qty_close = order.qty_close
                deal.side_close = order.side_close
                session.commit()
                print("♻️ Сделка обновлена в таблице deals.")
        except Exception as e:
            print(f"[update_deal] Ошибка: {e}")

    @staticmethod
    def get_earn(order_id: str):
        with (session_factory() as session):
            query = select(Deals).filter(Deals.order_id_close == order_id)
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
            query = (
                select(Coins)
                .where(Coins.in_deal > 0)
                .order_by(Coins.id)
            )
            res = session.execute(query)
            result = res.scalars().all()
            coins = []
            for coin in result:
                coins.append(coin.coin)
            return coins

    @staticmethod
    def delete_coin(coin: str):
        with session_factory() as session:
            query = (
                update(Coins)
                .where(Coins.coin == coin)
                .values(in_deal=Coins.in_deal - 1)
            )
            session.execute(query)
            session.commit()

    @staticmethod
    def add_coin(coin: str):
        with session_factory() as session:
            query = (
                update(Coins)
                .where(Coins.coin == coin)
                .values(in_deal=Coins.in_deal + 1)
            )
            session.execute(query)
            session.commit()