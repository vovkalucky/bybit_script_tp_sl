from classes.OrdersStructure import Order
from settings import PROJECT_NAME, MAX_COUNT_OF_DEALS
import requests
from config import TLG_TOKEN, TLG_ADMIN_ID

class TlgSendMessage:
    @staticmethod
    def send_tlg_message_new_tp_sl_order(order: Order) -> str:
        from db.queries.orm import DealsOrm
        from classes.SpotOrders import SpotOrders
        spot_orders = SpotOrders(symbol=order.symbol)
        trade_balance = spot_orders.get_trade_balance("USDT")
        message_title = f"{PROJECT_NAME}\n🔻 TP/SL ордер для {order.symbol} успешно размещен\n"
        list_of_open_deals = DealsOrm.select_open_deals()
        count_open_limit_orders = len(list_of_open_deals)
        url = f"https://api.telegram.org/bot{TLG_TOKEN}/sendMessage"
        message = (f"{message_title}\n"
                   f"status: {order.status}\n"
                   f"side: {order.side_open}\n"
                   f"tp: {order.take_profit}\n"
                   f"sl: {order.stop_loss}\n"
                   f"qty: {order.qty_open}\n"
                   f"order_id: {order.order_id_close}\n"
                   f"price: {order.price}\n"
                   f"money_open: {round(float(order.money_open), 3)}\n"
                   f"tax_open: {round(float(order.tax_open), 3)}\n\n"
                   f"Открытых позиций: {count_open_limit_orders}/{MAX_COUNT_OF_DEALS}\n"
                   f"Торговый баланс: {trade_balance}"
                   )
        payload = {
            "chat_id": TLG_ADMIN_ID,
            "text": message
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("✉️ Уведомление об установке ордера успешно отправлено.")
                return "✉️ Уведомление об установке ордера успешно отправлено."
            else:
                print(f"❗️Ошибка отправки уведомления: {response.status_code} {response.text}")
                return f"❗️Ошибка отправки уведомления: {response.status_code} {response.text}"
        except requests.exceptions.RequestException as e:
            print(f"❗️Ошибка соединения: {e}")
            return f"❗️Ошибка соединения: {e}"


    @staticmethod
    def send_tlg_message_close_tp_sl_order(order: Order) -> str:
        from db.queries.orm import DealsOrm
        from classes.SpotOrders import SpotOrders
        spot_orders = SpotOrders(symbol=order.symbol)
        trade_balance = spot_orders.get_trade_balance("USDT")
        earn = DealsOrm.get_earn(order.order_id)
        message_title = (f"{PROJECT_NAME}\n"
                         f"💰 Результат для {order.symbol}: {earn} $\n")
        list_of_open_deals = DealsOrm.select_open_deals()
        count_open_limit_orders = len(list_of_open_deals)
        url = f"https://api.telegram.org/bot{TLG_TOKEN}/sendMessage"
        message = (f"{message_title}\n"
                   f"status: {order.status}\n"
                   f"side: {order.side_close}\n"
                   f"qty: {order.qty_close}\n"
                   f"order_id: {order.order_id}\n"
                   f"price: {order.price}\n"
                   f"money_close: {round(float(order.money_close), 3)}\n"
                   f"tax_close: {round(float(order.tax_close), 3)}\n\n"
                   f"Открытых позиций: {count_open_limit_orders}/{MAX_COUNT_OF_DEALS}\n"
                   f"Торговый баланс: {trade_balance}"
                   )
        payload = {
            "chat_id": TLG_ADMIN_ID,
            "text": message
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("✉️ Уведомление о закрытии ордера успешно отправлено.")
                return "✉️ Уведомление о закрытии ордера успешно отправлено."
            else:
                print(f"❗️Ошибка отправки уведомления: {response.status_code} {response.text}")
                return f"❗️Ошибка отправки уведомления: {response.status_code} {response.text}"
        except requests.exceptions.RequestException as e:
            print(f"❗️Ошибка соединения: {e}")
            return f"❗️Ошибка соединения: {e}"