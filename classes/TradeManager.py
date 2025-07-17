from pybit import exceptions
from classes.SpotOrders import SpotOrders
from classes.TlgSendMessage import TlgSendMessage
from db.queries.orm import CoinsOrm, DealsOrm
from settings import MONEY_FOR_ONE_ORDER, TAKE_PROFIT, MAX_COUNT_OF_DEALS, STOP_LOSS
from classes.strategy.new_13_07_2025 import AnalysisCoin

class TradeManager:
    def __init__(self):
        self.coins = CoinsOrm.select_coins()

    @staticmethod
    def check_deal_limits() -> bool:
        spot_orders = SpotOrders(symbol="DOGEUSDT")
        list_of_deals = DealsOrm.select_open_deals()
        active_deals = spot_orders.check_orders_status(list_of_deals)
        if len(active_deals) >= MAX_COUNT_OF_DEALS:
            print(f"🤖 Бот уже участвует в {len(active_deals)} сделках(е)!\n"
                  f"⏳ Подождите, пока закроется хотя бы одна из них")
            return False
        return True

    def find_and_execute_trade(self) -> None:
        if not TradeManager.check_deal_limits():
            return
        for pair in self.coins:
            analysis = AnalysisCoin(pair)
            for timeframe in ["15", "30"]:
                side = analysis.analyze_coin(timeframe)
                if side in ["Buy", "Sell"]:
                    print(f"📣📣📣 Найден сигнал на {side} для {pair} на таймфрейме {timeframe}! 📣📣📣")
                    self.execute_trade(pair, side)
                    return  # Сигнал найден, прекращаем дальнейший поиск
        print(f"🔴 Сигнал не найден для {len(self.coins)} пар из списка: {self.coins}")


    @staticmethod
    def execute_trade(symbol: str, side: str):
        try:
            spot = SpotOrders(symbol=symbol)
            order_open = spot.tp_sl_order(side, MONEY_FOR_ONE_ORDER, TAKE_PROFIT, STOP_LOSS)
            if not order_open.order_id:
                return
            order = spot.get_info_about_tp_sl_order(order_open)
            if order:
                CoinsOrm.delete_coin(symbol)
                DealsOrm.append_deal(order)
                TlgSendMessage.send_tlg_message_new_tp_sl_order(order)

        except exceptions.InvalidRequestError as e:
            print("[execute_trade] ByBit API Request Error", e.status_code, e.message, sep=" | ")
        except exceptions.FailedRequestError as e:
            print("[execute_trade] HTTP Request Failed", e.status_code, e.message, sep=" | ")
        except Exception as e:
            print(f"[execute_trade] ❌ Ошибка при исполнении сделки для {symbol}: {e}")