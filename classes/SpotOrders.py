import time
from typing import Tuple, List, Optional
from pybit.unified_trading import HTTP
from classes.TlgSendMessage import TlgSendMessage
from classes.TradeHelpsFunctions import TradeHelpsFunc
from config import BYBIT_API_KEY, BYBIT_SECRET_KEY
from db.queries.orm import CoinsOrm, DealsOrm
from settings import DEMO_TRADE
from classes.OrdersStructure import LimitOrder, TpSlOrder, MarketOrder

class SpotOrders:
    session = HTTP(api_key=BYBIT_API_KEY,
                   api_secret=BYBIT_SECRET_KEY,
                   demo=DEMO_TRADE,
                   recv_window=10000,
                   max_retries=10,
                   retry_delay=10)

    def __init__(self, symbol): #side
        self.category = "spot"
        self.symbol = symbol
        self.price_decimals, self.qty_decimals, self.min_qty = self.get_filters()
        #self.side = side
        self.price = SpotOrders.get_current_price_of_coin(self.symbol)

    def get_filters(self) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """Функция для получения лимитов для конкретной монеты (coin_name).
        На выходе получаем price_decimals (точность для цены), qty_decimals (точность для количества монет)
        , min_qty (минимальное количество доступное для покупки)"""
        max_attempts = 3
        attempt_delay = 10  # seconds

        for attempt in range(1, max_attempts + 1):
            try:
                instruments = self.session.get_instruments_info(category=self.category)

                if not instruments or not isinstance(instruments, dict):
                    print(f"[get_filters] Attempt {attempt}: Invalid response format")
                    if attempt < max_attempts:
                        time.sleep(attempt_delay)
                    continue

                spot_list = instruments.get("result", {}).get("list", [])

                if not spot_list:
                    print(f"[get_filters] Attempt {attempt}: Empty spot list")
                    if attempt < max_attempts:
                        time.sleep(attempt_delay)
                    continue

                coin = next((x for x in spot_list if x.get("symbol") == self.symbol), None)

                if coin is None:
                    print(f"[get_filters] Attempt {attempt}: Coin {self.symbol} not found in spot list")
                    if attempt < max_attempts:
                        time.sleep(attempt_delay)
                    continue

                try:
                    qty_decimals = coin['lotSizeFilter']['basePrecision']
                    price_decimals = coin['priceFilter']['tickSize']
                    min_qty = coin['lotSizeFilter']['minOrderQty']

                    return (
                        TradeHelpsFunc.count_digits_after_decimal(price_decimals),
                        TradeHelpsFunc.count_digits_after_decimal(qty_decimals),
                        min_qty
                    )
                except KeyError as ke:
                    print(f"[get_filters] Attempt {attempt}: Missing expected key in coin data: {ke}")
                    return None, None, None

            except Exception as e:
                print(f"[get_filters] Attempt {attempt}: Exception: {e}")
                if attempt < max_attempts:
                    time.sleep(attempt_delay)

        return None, None, None

    @staticmethod
    @TradeHelpsFunc.retry()
    def get_current_price_of_coin(symbol: str) -> float:
        """
        Получает текущую цену монеты на спотовом рынке с повторными попытками.
        Args:
            symbol: Торговая пара (например, 'BTCUSDT')
        Returns:
            float: Текущая цена
        """
        response = SpotOrders.session.get_tickers(category="spot", symbol=symbol)
        try:
            price_str = response.get("result", {}).get("list", [{}])[0].get("lastPrice")
            #print(f"[get_current_price_of_coin] {price_str}")
            if not price_str:
                raise Exception("[get_current_price_of_coin] Price data not found in response")
            return float(price_str)

        except (IndexError, KeyError, TypeError, ValueError) as e:
            raise Exception(f"Error parsing response: {str(e)}")


    @TradeHelpsFunc.retry()  # Применяем декоратор с нужными параметрами
    def market_order(self, side: str, money_for_one_order: float) -> MarketOrder:
        """Установка market order на сумму qty ($)"""
        qty = TradeHelpsFunc.float_trunc(money_for_one_order, self.qty_decimals)

        order = self.session.place_order(
            category=self.category,
            symbol=self.symbol,
            side=side,
            orderType="Market",
            qty=qty,
            marketUnit="quoteCoin"
        )
        order_id = order.get('result', {}).get('orderId')
        order = MarketOrder(order_id=order_id)
        if not order_id:
            print(f"[market_order] No orderId in response")
            return None
        return order


    @TradeHelpsFunc.retry()  # Применяем декоратор с нужными параметрами
    def limit_order(self, side: str, money_or_qty: float, take_profit: float) -> LimitOrder:
        """Установка limit order на сумму qty ($).
        Возвращает id ордера"""

        # Получаем текущую цену
        current_price = SpotOrders.get_current_price_of_coin(self.symbol)

        # Если ордер на покупку
        if side == "Buy":
            print("Buy")

            # Рассчитываем количество монет, которое можно купить на заданную сумму
            qty = money_or_qty / current_price
            qty = TradeHelpsFunc.float_trunc(qty, self.qty_decimals)

            # Цена покупки (ниже текущей)
            price = current_price * (1 - take_profit / 100)
            price = TradeHelpsFunc.float_trunc(price, self.price_decimals)

        # Если ордер на продажу
        elif side == "Sell":
            print("Sell")

            # Количество монет для продажи (если у вас есть достаточное количество для продажи, например 100 монет)
            # Предполагается, что вы хотите продать все монеты, так что qty берется из текущего баланса.
            #qty = self.get_balance_of_coin(self.symbol)  # Предположим, что у вас есть метод для получения баланса
            qty = TradeHelpsFunc.float_trunc(money_or_qty, self.qty_decimals)

            # Цена продажи (выше текущей)
            price = current_price * (1 + take_profit / 100)
            price = TradeHelpsFunc.float_trunc(price, self.price_decimals)

        # Размещение лимитного ордера
        order = self.session.place_order(
            category=self.category,
            symbol=self.symbol,
            side=side,
            orderType="Limit",
            qty=qty,
            price=price,
            marketUnit="quoteCoin"
        )

        order_id = order.get('result', {}).get('orderId')
        order = LimitOrder(order_id=order_id)
        if not order_id:
            print(f"[limit_order] No orderId in response")
            return None
        return order

    @TradeHelpsFunc.retry()
    def get_info_about_limit_order(self, order: LimitOrder) -> LimitOrder:
        response_limit_order = self.session.get_open_orders(category=self.category, orderId=order.order_id)
        order = response_limit_order['result']['list'][0]
        #print(f"[get_info_about_limit_order]: {order}")
        status = order['orderStatus']
        #if status == "New":
        order = LimitOrder(order_id=order['orderId'], symbol=order['symbol'], qty=order['cumExecQty'],
                                 side=order['side'], status=status, close_price=order['avgPrice'], money_open=order['cumExecValue'],
                                 tax_open=str(float(order['cumExecFee']) * float(order['price'])), time_open=order['createdTime'],
                                 price=order['price']
        )
        return order

    @TradeHelpsFunc.retry()
    def get_info_about_market_order(self, order: MarketOrder) -> MarketOrder:
        response_open_orders = self.session.get_order_history(category=self.category, orderId=order.order_id)
        order = response_open_orders['result']['list'][0]
        print(f"[get_info_about_market_order]: {order}")
        status = order['orderStatus']
        # if status in ["Filled", "Deactivated"]:
        tax_open = str(round(float(order['cumExecFee']) * float(order['avgPrice']),3))
        order = MarketOrder(order_id=order['orderId'], symbol=order['symbol'], qty=order['cumExecQty'],
                           side=order['side'], status=status, close_price=order['avgPrice'], money_open=order['cumExecValue'],
                           tax_open=tax_open, time_open=order['createdTime']
                           )
        return order

    @TradeHelpsFunc.retry()
    def tp_sl_order(self, side: str, money_for_one_order: float, take_profit: float, stop_loss: float) -> TpSlOrder:
        """Установка limit order на сумму qty ($), с заданием Take Profit (%) и Stop Loss(%).
        Возвращает id ордера"""
        close_price = self.get_current_price_of_coin(self.symbol)
        qty = money_for_one_order/close_price
        qty = TradeHelpsFunc.float_trunc(qty, self.qty_decimals)
        take_profit_price = close_price * (1 + take_profit / 100)
        stop_loss_price = close_price * (1 - stop_loss / 100)
        tp_price = TradeHelpsFunc.float_trunc(take_profit_price, self.price_decimals)
        sl_price = TradeHelpsFunc.float_trunc(stop_loss_price, self.price_decimals)

        order = self.session.place_order(
            category=self.category,
            symbol=self.symbol,
            side=side,
            orderType="Limit",
            qty=qty,
            price=close_price,
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
        order_id = order.get('result', {}).get('orderId')
        order = TpSlOrder(order_id=order_id)
        if not order_id:
            print(f"[tp_sl_order] No orderId in response")
            return None
        return order

    @TradeHelpsFunc.retry()
    def find_tp_sl_order_id(self, take_profit_value: str) -> str:
        """Поиск TP/SL ордера по значению тейкпрофита (take_profit_value)"""
        try:
            response_tp_sl_orders = self.session.get_open_orders(category=self.category)
            tp_sl_orders = response_tp_sl_orders["result"]["list"]
            tp_sl_order_list = [order for order in tp_sl_orders if order.get("takeProfit") == str(take_profit_value)]
            return tp_sl_order_list[0]["orderId"]
        except Exception as e:
            print(f"[find_tp_sl_order] Exception: {e}")
            return None

    @TradeHelpsFunc.retry()
    def get_info_about_tp_sl_order(self, order: TpSlOrder) -> TpSlOrder:
            response_limit_order = self.session.get_open_orders(category=self.category, orderId=order.order_id)
            order = response_limit_order['result']['list'][0]
            print(f"[get_info_about_tp_sl_order]: {order}")
            order_id_close = self.find_tp_sl_order_id(order['takeProfit'])
            response_tp_sl_order = self.session.get_open_orders(category=self.category, orderId=order_id_close)
            status_tp_sl_order = response_tp_sl_order['result']['list'][0]['orderStatus']
            tax_open = str(round(float(order['cumExecFee']) * float(order['price']),3))
            order = TpSlOrder(order_id=order['orderId'], symbol=order['symbol'], qty=order['cumExecQty'],
                                     side=order['side'], status=status_tp_sl_order, close_price=order['avgPrice'], money_open=order['cumExecValue'],
                                     tax_open=tax_open, time_open=order['createdTime'],
                                     price=order['price'], take_profit=order['takeProfit'], stop_loss=order['stopLoss'],
                                     order_id_close=order_id_close, money_close="0", tax_close="0"
            )
            print(f"get_info_about_tp_sl_order {order}")

            # CoinsOrm.delete_coin(order.symbol)
            # DealsOrm.append_deal(coin=order.symbol, order_id_open=order.order_id,
            #                      order_id_close=order.tp_sl_order_id,
            #                      money_open=order.money_open, tax_open=order.tax_open,
            #                      status=order.status, money_close=order.money_close, tax_close=order.tax_close)
            # TlgSendMessage.send_tlg_message_new_tp_sl_order(order)

            return order

    @TradeHelpsFunc.retry()
    def check_orders_status(self, orders: List[str]) -> List[str]:
        for order_id in orders:
            response_open_orders = self.session.get_order_history(category=self.category, orderId=order_id)
            time.sleep(1)
            if len(response_open_orders['result']['list']) == 0:
                continue
            order = response_open_orders['result']['list'][0]
            status = order['orderStatus']
            if status in ["Filled", "Deactivated"]:
                order = TpSlOrder(order_id=order['orderId'], symbol=order['symbol'], qty=order['cumExecQty'],
                                  side=order['side'], status=status, close_price=order['avgPrice'],
                                  money_close=order['cumExecValue'], tax_close=order['cumExecFee'],
                                  order_id_close=order_id, price=order['price'],
                                  basePrice=order['basePrice'], triggerPrice=order['triggerPrice']
                                  )
                CoinsOrm.add_coin(order.symbol)
                DealsOrm.update_deal(order)
                TlgSendMessage.send_tlg_message_close_tp_sl_order(order)
        return orders


# spot = SpotOrders(symbol="PEPEUSDT")
#print(spot.qty_decimals)
# order = spot.tp_sl_order("Buy", 50, 4,4)
# print(order)
# order = TpSlOrder(order_id='1917142573705858304')
# info = spot.get_info_about_tp_sl_order(order)
# print(info)
