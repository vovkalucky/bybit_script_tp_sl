import time
from typing import Tuple, List, Optional
from pybit.unified_trading import HTTP
from classes.TlgSendMessage import TlgSendMessage
from classes.TradeHelpsFunctions import TradeHelpsFunc
from config import get_config
from classes.OrdersStructure import Order
from settings import TAKER_FEE, SLIPPAGE


class SpotOrders:
    def __init__(self, symbol):
        config = get_config()
        self.session = HTTP(api_key=config['api_key'],
                            api_secret=config['api_secret'],
                            demo=config['demo'],
                            recv_window=10000,
                            max_retries=10,
                            retry_delay=10)
        self.category = "spot"
        self.symbol = symbol
        self.price_decimals, self.qty_decimals, self.min_qty = self.get_filters()
        self.price = self.get_current_price_of_coin()

    def get_filters(self) -> Tuple[Optional[int], Optional[int], Optional[float]]:
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
                        float(min_qty)
                    )
                except KeyError as ke:
                    print(f"[get_filters] Attempt {attempt}: Missing expected key in coin data: {ke}")
                    return None, None, None

            except Exception as e:
                print(f"[get_filters] Attempt {attempt}: Exception: {e}")
                if attempt < max_attempts:
                    time.sleep(attempt_delay)

        return None, None, None


    def get_current_price_of_coin(self) -> float:
        """
        Получает текущую цену монеты на спотовом рынке.
        Args:
            self.symbol: Торговая пара (например, 'BTCUSDT')
        Returns:
            price_str: Текущая цена
        """
        response = self.session.get_tickers(category="spot", symbol=self.symbol)
        try:
            price_str = response.get("result", {}).get("list", [{}])[0].get("lastPrice")
            if not price_str:
                raise Exception("[get_current_price_of_coin] Цена не найдена")
            return float(price_str)

        except (IndexError, KeyError, TypeError, ValueError) as e:
            raise Exception(f"[get_current_price_of_coin] {e}")


    @TradeHelpsFunc.retry()
    def market_order(self, side: str, money_for_one_order: float) -> Order:
        """Установка market order"""
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
        order = Order(order_id=order_id)
        if not order_id:
            print(f"[market_order] No orderId in response")
            return Order()
        return order

    @TradeHelpsFunc.retry()
    def limit_order(self, side: str, money_or_qty: float, take_profit: float) -> Order:
        """
        Установка лимитного ордера на сумму в quote (для Buy) или количество монет (для Sell).
        Возвращает LimitOrder с order_id.
        """

        # Получаем текущую цену
        current_price = self.price

        # Определяем лимитную цену и количество
        if side == "Buy":
            # Лимитная цена ниже текущей
            price = current_price * (1 - take_profit / 100)
            price = TradeHelpsFunc.float_trunc(price, self.price_decimals)

        elif side == "Sell":
            # Цена продажи выше текущей
            price = current_price * (1 + take_profit / 100)
            price = TradeHelpsFunc.float_trunc(price, self.price_decimals)

        else:
            print("[limit_order] Ошибка в параметре side")
            return Order()

        qty = money_or_qty / float(price)
        qty = TradeHelpsFunc.float_trunc(qty, self.qty_decimals)


        if float(qty) < self.min_qty:
            print(f"[limit_order] Кол-во {qty} меньше min_qty {self.min_qty} для {self.symbol}")
            return Order()

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
        order = Order(order_id=order_id)

        if not order_id:
            print(f"[limit_order] No orderId in response")
            return Order()

        return order

    @TradeHelpsFunc.retry()
    def get_info_about_limit_order(self, order: Order) -> Order:
        response_limit_order = self.session.get_open_orders(category=self.category, orderId=order.order_id)
        order = response_limit_order['result']['list'][0]
        status = order['orderStatus']
        order = Order(order_id=order['orderId'], symbol=order['symbol'], qty_open=order['cumExecQty'],
                      side_open=order['side'], status=status, avgPrice=order['avgPrice'], money_open=order['cumExecValue'],
                      tax_open=str(float(order['cumExecFee']) * float(order['price'])), time_open=order['createdTime'],
                      price=order['price']
                      )
        return order

    @TradeHelpsFunc.retry()
    def get_info_about_market_order(self, order: Order) -> Order:
        response_open_orders = self.session.get_order_history(category=self.category, orderId=order.order_id)
        order = response_open_orders['result']['list'][0]
        print(f"[get_info_about_market_order]: {order}")
        status = order['orderStatus']
        tax_open = order['cumExecFee']
        if order['side'] == "Buy":
            tax_open = str(round(float(order['cumExecFee']) * float(order['avgPrice']),3))
        order = Order(order_id=order['orderId'], symbol=order['symbol'], qty_open=order['cumExecQty'],
                      side_open=order['side'], status=status, avgPrice=order['avgPrice'], money_open=order['cumExecValue'],
                      tax_open=tax_open, time_open=order['createdTime']
                      )
        return order

    def tp_sl_order(self, side: str, money_for_one_order: float, take_profit: float, stop_loss: float = 0) -> Order:
        """Установка limit order на сумму qty ($), с заданием Take Profit (%) и Stop Loss(%).
        Возвращает id ордера"""
        close_price = self.price
        qty = money_for_one_order / close_price
        qty = TradeHelpsFunc.float_trunc(qty, self.qty_decimals)
        if side == "Buy":
            take_profit_price = close_price * (1 + take_profit / 100)
            stop_loss_price = close_price * (1 - stop_loss / 100)
        elif side == "Sell":
            take_profit_price = close_price * (1 - take_profit / 100)
            stop_loss_price = close_price * (1 + stop_loss / 100)
        else:
            print(f"[tp_sl_order] Invalid side: {side}")
            return Order()

        tp_price = TradeHelpsFunc.float_trunc(take_profit_price, self.price_decimals)
        sl_price = TradeHelpsFunc.float_trunc(stop_loss_price, self.price_decimals)

        try:
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
                slLimitPrice=sl_price,
                tpLimitPrice=tp_price,
                tpOrderType="Limit",
                slOrderType="Limit",
                orderFilter = "OCO",  #OCO Фильтр для OCO-ордера
                timeInForce = "GTC"  # "Good Till Cancel" - ордер действует до отмены
            )
            time.sleep(5)
            order_id = order.get('result', {}).get('orderId')
            if not order_id:
                print(f"[tp_sl_order] No orderId in response")
                return Order()
            if self.check_order_status(order_id, "Filled"):
                print(f"[tp_sl_order] {order_id}")
                order = Order(order_id=order_id, status="Filled")
                return order
            else:
                self.cancel_order(order_id)
                return Order()
        except Exception as e:
            print(f"[tp_sl_order] {e}")
            return Order()

    @TradeHelpsFunc.retry_until_true(6,10)
    def check_order_status(self, order_id: str, status: str) -> bool:
        try:
            order = self.session.get_open_orders(category=self.category, orderId=order_id)
            order = order['result']['list'][0]
            print(f"[check_order_status] {order['symbol']} {order['orderId']} {order['orderStatus']}")
            if order['orderStatus'] == status:
                return True
            else:
                return False
        except Exception as e:
            print(f"[check_order_status] Ордер не найден: {e}")
            return False

    @TradeHelpsFunc.retry()
    def find_open_order_id_by_tp(self, take_profit_value: str) -> str:
        """Поиск TP/SL ордера по значению тейкпрофита (take_profit_value)"""
        try:
            response_tp_sl_orders = self.session.get_open_orders(category=self.category)
            tp_sl_orders = response_tp_sl_orders["result"]["list"]
            #print(f"[find_open_order_id_by_tp] {tp_sl_orders}")
            tp_sl_order_list = [order for order in tp_sl_orders if order.get("takeProfit") == str(take_profit_value)]
            #print(f"[find_open_order_id_by_tp] Нужный ордер? {tp_sl_order_list[0]["orderId"]}")
            return tp_sl_order_list[0]["orderId"]
        except Exception as e:
            print(f"[find_open_order_id_by_tp] Exception: {e}")
            return ""

    @TradeHelpsFunc.retry()
    def find_open_order_id_by_name(self, status: str) -> str:
        """Поиск открытого TP/SL ордера по названию монеты"""
        try:
            response_tp_sl_orders = self.session.get_open_orders(category=self.category)
            tp_sl_orders = response_tp_sl_orders["result"]["list"]
            tp_sl_order_list = [order for order in tp_sl_orders if order.get("symbol") == status]
            return tp_sl_order_list[0]["orderId"]
        except Exception as e:
            print(f"[find_open_order_id_by_name] Exception: {e}")
            return ""

    @TradeHelpsFunc.retry()
    def get_info_about_tp_sl_order(self, order: Order) -> Order:
            response_limit_order = self.session.get_open_orders(category=self.category, orderId=order.order_id)
            order = response_limit_order['result']['list'][0]
            #print(f"[get_info_about_tp_sl_order] order: {order}")
            order_id_close = self.find_open_order_id_by_tp(order['takeProfit'])
            print(f"[get_info_about_tp_sl_order] Открыт ордер на закрытие сделки: {order_id_close}")
            #order_id_close = self.find_open_order_id_by_name(order['symbol'])
            response_tp_sl_order = self.session.get_open_orders(category=self.category, orderId=order_id_close)
            status_tp_sl_order = response_tp_sl_order['result']['list'][0]['orderStatus']
            if order['side'] == "Buy":
                tax_open = str(round(float(order['cumExecFee']) * float(order['price']), 4))
            else:
                tax_open = str(round(float(order['cumExecFee']), 4))
            order = Order(order_id=order['orderId'], symbol=order['symbol'], qty_open=order['cumExecQty'],  #qty=order['cumExecQty']
                          side_open=order['side'], status=status_tp_sl_order, avgPrice=order['avgPrice'],
                          money_open=order['cumExecValue'],
                          tax_open=tax_open, time_open=order['createdTime'],
                          price=order['price'], take_profit=order['takeProfit'], stop_loss=order['stopLoss'],
                          order_id_close=order_id_close, money_close="0", tax_close="0"
                          )
            return order

    @TradeHelpsFunc.retry()
    def check_orders_status(self, orders: List[str]) -> List[str]:
        """Проверка статуса ордеров из списка orders, которые подгружаются из БД"""
        from db.queries.orm import CoinsOrm, DealsOrm
        try:
            for order_id in orders:
                response_open_orders = self.session.get_order_history(category=self.category, orderId=order_id)
                time.sleep(1)
                if len(response_open_orders['result']['list']) == 0:
                    continue
                order = response_open_orders['result']['list'][0]
                status = order['orderStatus']
                if status in ["Filled", "Deactivated"]:
                    if order['side'] == "Buy":
                        tax_close = str(round(float(order['cumExecFee']) * float(order['price']), 4))
                    else:
                        tax_close = str(round(float(order['cumExecFee']), 4))
                    print(f"[check_orders_status] {order['symbol']} {order['orderId']} {order['orderStatus']}")
                    order = Order(order_id=order['orderId'], symbol=order['symbol'], qty_close=order['cumExecQty'],
                                  side_close=order['side'], status=status, avgPrice=order['avgPrice'],
                                  money_close=order['cumExecValue'], tax_close=tax_close,
                                  order_id_close=order_id, price=order['price'], triggerPrice=order['triggerPrice']
                                  )
                    CoinsOrm.delete_coin(order.symbol)
                    DealsOrm.update_deal(order)
                    TlgSendMessage.send_tlg_message_close_tp_sl_order(order)
            return orders
        except Exception as e:
            print(f"[check_orders_status] Ордера не найдены: {e}")
            return orders


    def cancel_order(self, order_id: str) -> bool:
        """Отмена открытого (незаполненного) ордера по order_id"""
        try:
            canceled_order = self.session.cancel_order(category="spot", orderId=order_id)
            if canceled_order['retMsg'] == "OK":
                print(f"[cancel_order] Ордер {order_id} успешно отменен")
                return True
            else:
                return False
        except Exception as e:
            print(f"[cancel_order] Ошибка при отмене ордера {order_id}: {e}")
            return False

    def get_trade_balance(self, coin) -> float:
        try:
            data = self.session.get_wallet_balance(accountType="UNIFIED", coin=coin)
            wallet_balance = round(float(data["result"]["list"][0]["coin"][0]["walletBalance"]), 2)
            return wallet_balance
        except Exception as e:
            print(f"[get_trade_balance] Ошибка при попытке получить баланс: {e}")
            return 0.0

