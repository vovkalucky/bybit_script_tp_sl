import time
from pybit import exceptions
from classes.SpotOrders import SpotOrders
from db.queries.orm import CoinsOrm, DealsOrm
from settings import MONEY_FOR_ONE_ORDER, TAKE_PROFIT, MAX_COUNT_OF_DEALS, STOP_LOSS
from classes.analysis.AnalysisCoin_imbalance_trend import AnalysisCoin

class TradeManager:
    def __init__(self):
        self.coins = CoinsOrm.select_coins()

    @staticmethod
    def check_deal_limits() -> bool:
        spot_orders = SpotOrders(symbol="DOGEUSDT")
        list_of_deals = DealsOrm.select_open_deals()
        active_deals = spot_orders.check_limits_orders_status(list_of_deals)
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
            if analysis.has_trade_signal():
                print(f"🎯🎯🎯 Найден сигнал для {pair}! 🎯🎯🎯")
                self.execute_trade(pair)
                return

        print(f"🔴 Сигнал не найден для {len(self.coins)} пар из списка: {self.coins}")

    @staticmethod
    def execute_trade(symbol, side):
        try:
            spot = SpotOrders(symbol=symbol, side=side)
            spot.get_current_price_of_coin(symbol)
            limit_order_buy = spot.limit_order_with_tp_sl(MONEY_FOR_ONE_ORDER, TAKE_PROFIT, STOP_LOSS)
            if not limit_order_buy:
                return
            if not spot.limit_order_with_tp_sl_retry:
                spot.cancel_order(limit_order_buy)
                return
            spot.get_info_about_limit_order()
            time.sleep(2)
            spot.get_info_about_tp_sl_order()

        except exceptions.InvalidRequestError as e:
            print("[execute_trade] ByBit API Request Error", e.status_code, e.message, sep=" | ")
        except exceptions.FailedRequestError as e:
            print("[execute_trade] HTTP Request Failed", e.status_code, e.message, sep=" | ")
        except Exception as e:
            print(f"[execute_trade] ❌ Ошибка при исполнении сделки для {symbol}: {e}")