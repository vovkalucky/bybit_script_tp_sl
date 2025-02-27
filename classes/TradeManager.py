import time
from pybit import exceptions
from classes.CoinsClass import CoinsClass
from classes.WorkWithCSV import WorkWithCSV
from classes.SpotOrders import SpotOrders
from settings import MONEY_FOR_ONE_ORDER, TAKE_PROFIT, MAX_COUNT_OF_DEALS
from classes.analysis.AnalysisCoin_imbalance_27_02_25 import AnalysisCoin


class TradeManager(CoinsClass, WorkWithCSV):

    #coins = CoinsClass.load_coins()

    def __init__(self):
        super().__init__()
        self.state = WorkWithCSV.load_deals()
        self.list_of_deals = self.state.get("list_of_deals", [])
        self.coins = CoinsClass.load_coins()


    def check_deal_limits(self) -> bool:
        spot_orders = SpotOrders(coin_name="DOGEUSDT")
        active_deals = spot_orders.check_limits_orders_status(self.list_of_deals)
        if len(active_deals) >= MAX_COUNT_OF_DEALS:
            print(f"🤖 Бот уже участвует в {len(active_deals)} сделках(е)!\n"
                  f"⏳ Подождите, пока закроется хотя бы одна из них")
            return False
        return True

    def find_and_execute_trade(self) -> None:
        if not self.check_deal_limits():
            return
        for pair in self.coins:
            analysis = AnalysisCoin(pair)
            if analysis.has_trade_signal():
                print(f"🎯🎯🎯 Найден сигнал для {pair} на всех таймфреймах! 🎯🎯🎯")
                self.execute_trade(pair)
                return

        print(f"🔴 Сигнал не найден для всех пар из списка: {self.coins}")

    @staticmethod
    def execute_trade(pair):
        try:
            spot = SpotOrders(coin_name=pair)
            spot.get_current_price_of_coin()
            limit_order_buy = spot.limit_order_with_tp_sl(MONEY_FOR_ONE_ORDER, TAKE_PROFIT)
            if not limit_order_buy:
                return
            if not spot.limit_order_with_tp_sl_retry:
                spot.cancel_order(limit_order_buy)
                return
            spot.get_info_about_limit_order()
            time.sleep(2)
            spot.get_info_about_tp_sl_order()

        except exceptions.InvalidRequestError as e:
            print("ByBit API Request Error", e.status_code, e.message, sep=" | ")
        except exceptions.FailedRequestError as e:
            print("HTTP Request Failed", e.status_code, e.message, sep=" | ")
        except Exception as e:
            print(f"❌ Ошибка при исполнении сделки для {pair}: {e}")