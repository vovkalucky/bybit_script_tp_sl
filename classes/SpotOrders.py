import time
from typing import Tuple, List
from pybit import exceptions
from pybit.unified_trading import HTTP
from classes.TlgSendMessage import TlgSendMessage
# from classes.WorkWithCSV import WorkWithCSV
# from classes.CoinsClass import CoinsClass
from config import BYBIT_API_KEY, BYBIT_SECRET_KEY
from db.queries.orm import CoinsOrm, DealsOrm
from settings import DEMO_TRADE, STOP_LOSS


class SpotOrders:
    session = HTTP(api_key=BYBIT_API_KEY,
                   api_secret=BYBIT_SECRET_KEY,
                   demo=DEMO_TRADE,
                   recv_window=10000,
                   max_retries=10,
                   retry_delay=10)

    #coins = CoinsClass.load_coins()
    #coins = CoinsOrm.select_coins()
    def __init__(self, coin_name):
        super().__init__()
        #self.state = WorkWithCSV.load_deals()
        #self.list_of_deals = self.state.get("list_of_deals", [])
        #self.list_of_deals = ListOfOpenDealsOrm.select_all_deals()
        self.category = "spot"
        self.coin_name = coin_name #это для пустого объекта для проверки статуса ордеров
        self.price_decimals, self.qty_decimals, self.min_qty = self.get_filters()
        self.symbol = self.qty = None
        self.order_id_buy = self.side_buy = self.close_price_buy = self.money_buy = self.status_buy = self.tax_buy = self.basePrice = None
        self.tax_buy_in_qty = self.time_buy = None
        self.orderLinkId = self.tp = self.sl = None
        self.order_id_sell = self.side_sell = self.close_price_sell = self.money_sell = self.status_sell = self.tax_sell = None
        self.earn = None
        self.time_sell = self.time_close = None
        self.triggerPrice = None


    def get_current_price_of_coin(self) -> float:
        response = SpotOrders.session.get_tickers(category="spot", symbol=self.coin_name)
        # Извлекаем актуальную цену
        if "result" in response and "list" in response["result"] and response["result"]["list"]:
            price = response["result"]["list"][0]["lastPrice"]
            #print(f"Актуальная цена {self.coin_name}: {price}, {type(price)}")
            #self.close_price_buy = float(price)
            return float(price)
        else:
            print("(get_current_price_of_coin) Ошибка при получении данных")

    @staticmethod
    def count_digits_after_decimal(str_number: str) -> int:
        # Проверяем, есть ли точка в числе
        if '.' in str_number:
            # Разделяем строку на целую и дробную части
            integer_part, decimal_part = str_number.split('.')
            return len(decimal_part)  # Возвращаем длину дробной части
        else:
            return 0  # Если точки нет, то цифр после запятой нет

    @staticmethod
    def float_trunc(f: float, prec: int) -> str:
        """Отбросить от float лишние знаки без округлений, включая числа в научной нотации"""
        float_value = float(f)
        # Преобразуем число в строку в стандартной десятичной записи
        l, r = f"{float_value:.{prec + 12}f}".split('.')  # Увеличиваем точность для предотвращения потерь
        return f'{l}.{r[:prec]}'  # Возвращаем строку для точного результата

    def check_limits_orders_status(self, orders: List[str]) -> List[str]:
        orders_to_remove = []
        #response_open_orders = self.session.get_order_history(category=self.category)
        #print(response_open_orders)
        for order_id in orders:
            try:
                response_open_orders = self.session.get_order_history(category=self.category, orderId=order_id)
                time.sleep(1)
                #print(f"(response_open_orders) {response_open_orders}")
                if len(response_open_orders['result']['list']) == 0:
                    continue
                open_order = response_open_orders['result']['list'][0]
                status = open_order['orderStatus']
                if status in ["Filled", "Deactivated"]:
                    print(f"(open_order) Filled! {open_order}")
                    self.qty = open_order['cumExecQty']
                    self.status_sell = status
                    self.order_id_sell = order_id
                    self.close_price_sell = open_order['avgPrice']
                    self.money_sell = open_order['cumExecValue']
                    self.tax_sell = open_order['cumExecFee']
                    self.symbol = open_order['symbol']
                    self.side_sell = open_order['side']
                    self.time_sell = open_order['createdTime']
                    self.time_close = open_order['updatedTime']
                    self.tp = open_order['tpLimitPrice']
                    self.sl = open_order['slLimitPrice']
                    self.basePrice = open_order['basePrice']
                    self.triggerPrice = open_order['triggerPrice']
                    #CoinsClass.add_coin(SpotOrders.coins, self.symbol)
                    CoinsOrm.add_coin(self.symbol)
                    #orders_to_remove.append(order_id)
                    #ListOfOpenDealsOrm.delete_deal(order_id)
                    #WorkWithCSV.update_order_to_csv(self)
                    DealsOrm.update_deal(coin=self.symbol, status=self.status_sell,
                                         money_sell=self.money_sell, tax_sell=self.tax_sell)
                    TlgSendMessage.send_tlg_message_close_tp_sl_order(self)
            except Exception as e:
                print(f"(check_limits_orders_status) Exception: {e}")

        #Удаляем все заказы со статусом "Filled" and "Cancelled"
        #for order_id in orders_to_remove:
            #orders.remove(order_id)
        #WorkWithCSV.save_deals({"list_of_deals": orders})
        print(f"📄 Список открытых лимитных ордеров {orders}")
        return orders


    def get_filters(self) -> Tuple[int, int, str]:
        """Функция для получения лимитов для конкретной монеты (coin_name).
        На выходе получаем price_decimals (точность для цены), qty_decimals (точность для количества монет)
        , min_qty (минимальное количество доступное для покупки)"""
        try:
            instruments = self.session.get_instruments_info(category=self.category)
            spot_list = instruments["result"]["list"]
            # print(f"Found a total of {len(spotList)} spot symbols.")
            coin = next((x for x in spot_list if x["symbol"] == self.coin_name), None)
            qty_decimals = coin['lotSizeFilter']['basePrecision']
            price_decimals = coin['priceFilter']['tickSize']
            min_qty = coin['lotSizeFilter']['minOrderQty']
            return (SpotOrders.count_digits_after_decimal(price_decimals),
                    SpotOrders.count_digits_after_decimal(qty_decimals), min_qty)
        except Exception as e:
            print(f"(get_filters) Exception:  {e}")

    def cancel_order(self, order_id: str) -> str:
        try:
            canceled_order = self.session.cancel_order(category="spot", orderId=order_id) #, symbol=self.symbol,
            if canceled_order['retMsg'] == "OK":
                return f"Ордер {order_id} успешно отменен"
        except Exception as e:
            print(f"(cancel_order) Exception: {e}")

    def limit_order_with_tp_sl(self, money_for_one_order: float, percent_of_earn: float) -> str:
        """Установка limit order на сумму qty $, 3 попытки (max_retries) получить состояние статуса
         с паузой (retry_delay) 15 сек. Если order не заполнен (FILLED) возвращаем False"""
        self.side_buy = "Buy"
        self.close_price_buy = self.get_current_price_of_coin()
        qty = money_for_one_order/self.close_price_buy
        qty = SpotOrders.float_trunc(qty, self.qty_decimals)
        take_profit_price = self.close_price_buy * percent_of_earn
        stop_loss_price = self.close_price_buy * STOP_LOSS
        tp_price = SpotOrders.float_trunc(take_profit_price, self.price_decimals)
        sl_price = SpotOrders.float_trunc(stop_loss_price, self.price_decimals)

        #tp_trigger_price = SpotOrders.float_trunc(float(tp_price) * 0.99, self.price_decimals)
        #sl_trigger_price = SpotOrders.float_trunc(float(sl_price) * 0.99, self.price_decimals)

        try:
            limit_order = self.session.place_order(
                category=self.category,
                symbol=self.coin_name,
                side=self.side_buy,
                orderType="Limit", #limit
                qty=qty,
                price=self.close_price_buy,
                marketUnit="quoteCoin",
                takeProfit=tp_price, #она же и тригерная цена. tpTriggerPrice не нужен!
                stopLoss=sl_price,
                # slTriggerPrice=sl_trigger_price,
                # tpTriggerPrice=tp_trigger_price,
                slLimitPrice=sl_price,
                tpLimitPrice=tp_price,
                tpOrderType="Limit",
                slOrderType="Limit",
                orderFilter = "OCO",  # Фильтр для OCO-ордера
                timeInForce = "GTC"  # "Good Till Cancel" - ордер действует до отмены
            )
            time.sleep(2)
            self.order_id_buy = limit_order['result']['orderId']
            return self.order_id_buy

        except exceptions.InvalidRequestError as e:
            print("(limit_order_with_tp_sl_retry) ByBit API Request Error", e.status_code, e.message, sep=" | ")
        except exceptions.FailedRequestError as e:
            print("(limit_order_with_tp_sl_retry) HTTP Request Failed", e.status_code, e.message, sep=" | ")
        except Exception as e:
            print(f"(limit_order_with_tp_sl_retry) Other exception: {e}")


    def limit_order_with_tp_sl_retry(self, max_retries: int = 3, retry_delay: int = 15) -> bool:
        retries = 0
        while retries < max_retries:
            try:
                open_orders = self.session.get_open_orders(category=self.category, orderId=self.order_id_buy)
                status_order_buy = open_orders['result']['list'][0]['orderStatus']
                if status_order_buy == "Filled":
                    return True
                else:
                    print(f"🛑 Лимитный ордер не заполнен!\n"
                          f"⏰ Попытка {retries + 1} не удалась. Проверка через {retry_delay} секунд.")
                    time.sleep(retry_delay)
                    retries += 1

            except exceptions.InvalidRequestError as e:
                print("(limit_order_with_tp_sl_retry) ByBit API Request Error", e.status_code, e.message, sep=" | ")
            except exceptions.FailedRequestError as e:
                print("(limit_order_with_tp_sl_retry) HTTP Request Failed", e.status_code, e.message, sep=" | ")
            except Exception as e:
                print(f"(limit_order_with_tp_sl_retry) Other exception: {e}")
        return False

    def get_info_about_limit_order(self) -> bool:
        try:
            if self.order_id_buy is None:
                print("‼️ Лимитный ордер не размещен! Проставь его самостоятельно!")
                return False
            response_limit_order = self.session.get_open_orders(category=self.category, orderId=self.order_id_buy)
            limit_order = response_limit_order['result']['list'][0]
            print(f"(get_info_about_limit_order): {limit_order}")
            status = limit_order['orderStatus']
            if status == "Filled":
                self.qty = limit_order['cumExecQty']
                self.status_buy = status
                self.close_price_buy  = limit_order['avgPrice']
                self.money_buy  = limit_order['cumExecValue']
                self.tax_buy = float(limit_order['cumExecFee']) * float(limit_order['price'])
                self.symbol = limit_order['symbol']
                self.side_buy = limit_order['side']
                self.time_buy = limit_order['createdTime']
                #self.tp = limit_order['takeProfit']
                self.tp = limit_order['tpLimitPrice']
                #self.sl = limit_order['stopLoss']
                self.sl = limit_order['slLimitPrice']
                return True
                # print(f"(get_info_about_limit_order) {self.qty} {self.status_buy} {self.close_price_buy} {self.money_buy} "
                #       f"{self.tax_buy} {self.symbol} {self.side_buy} {self.time_buy}")

        except Exception as e:
            print(f"(get_info_about_limit_order) Exception: {e}")

    def find_tp_sl_order(self, take_profit_value: str) -> str:
        try:
            response_tp_sl_orders = self.session.get_open_orders(category=self.category)
            print(f"(response_tp_sl_orders) {response_tp_sl_orders}")
            tp_sl_orders = response_tp_sl_orders["result"]["list"]
            #tp_sl_order_list = [order for order in tp_sl_orders if order.get("takeProfit") == str(take_profit_value)]
            tp_sl_order_list = [order for order in tp_sl_orders if order.get("tpLimitPrice") == str(take_profit_value)]
            return tp_sl_order_list[0]
        except Exception as e:
            print(f"(find_tp_sl_order) Exception: {e}")
            return "Order not find"



    def get_info_about_tp_sl_order(self) -> bool:
        try:
            tp_sl_order = self.find_tp_sl_order(self.tp)
            print(f"(get_info_about_tp_sl_order): {tp_sl_order}")
            if tp_sl_order == "Order not find":
                return False
            status = tp_sl_order['orderStatus']
            if status == "Untriggered": #or status == "Active"
                self.order_id_sell = tp_sl_order['orderId']
                self.qty = tp_sl_order['cumExecQty']
                self.status_sell = status
                self.close_price_sell = tp_sl_order['avgPrice']
                self.money_sell = tp_sl_order['cumExecValue']
                self.tax_sell = tp_sl_order['cumExecFee']
                self.basePrice = tp_sl_order['basePrice']
                self.symbol = tp_sl_order['symbol']
                self.side_sell = tp_sl_order['side']
                self.time_sell = tp_sl_order['createdTime']
                #self.tp = tp_sl_order['takeProfit']
                self.tp = tp_sl_order['tpLimitPrice']
                #self.sl = tp_sl_order['stopLoss']
                self.sl = tp_sl_order['slLimitPrice']
                #self.list_of_deals.append(self.order_id_sell)
                #ListOfOpenDealsOrm.append_deal(self.symbol, self.order_id_sell)

                #WorkWithCSV.save_deals({"list_of_deals": self.list_of_deals})
                #CoinsClass.remove_coin(SpotOrders.coins, self.symbol)
                CoinsOrm.delete_coin(self.symbol)
                DealsOrm.append_deal(coin=self.symbol,order_id_buy=self.order_id_buy, order_id_sell=self.order_id_sell,
                                     money_buy=self.money_buy, tax_buy=self.tax_buy, money_sell=self.money_sell,
                                     tax_sell=self.tax_sell, status=self.status_sell)
                TlgSendMessage.send_tlg_message_new_tp_sl_order(self)
                return True
        except Exception as e:
            print(f"(get_info_about_tp_sl_order) Exception: {e}")

    @classmethod
    def get_order_book(cls, symbol):
        """Получение стакана ордеров"""
        return cls.session.get_orderbook(
            category="spot",
            symbol=symbol,
            limit=50
        )


