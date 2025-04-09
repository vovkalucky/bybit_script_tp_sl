from classes.OrdersStructure import Order
from db.queries.orm import DealsOrm
from settings import PROJECT_NAME
import requests
from config import TLG_TOKEN, TLG_ADMIN_ID

class TlgSendMessage:
    @staticmethod
    def send_tlg_message_new_tp_sl_order(order: Order) -> None:
        message_title = f"{PROJECT_NAME}\n🔻 TP/SL ордер для {order.symbol} успешно размещен\n"
        list_of_open_deals = DealsOrm.select_open_deals()
        count_open_limit_orders = len(list_of_open_deals)
        url = f"https://api.telegram.org/bot{TLG_TOKEN}/sendMessage"
        message = (f"{message_title}\n"
                   f"status: {order.status}\n"
                   f"side: {order.side}\n"
                   f"tp: {order.take_profit}\n"
                   f"sl: {order.stop_loss}\n"
                   f"qty: {order.qty}\n"
                   f"order_id: {order.order_id_close}\n"
                   f"price: {order.price}\n"
                   f"money_open: {round(float(order.money_open), 3)}\n"
                   f"tax_open: {round(float(order.tax_open), 3)}\n\n"
                   f"Открытых позиций: {count_open_limit_orders}"
                   )
        payload = {
            "chat_id": TLG_ADMIN_ID,
            "text": message
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("✉️ Уведомление об установке ордера успешно отправлено.")
            else:
                print(f"❗️Ошибка отправки уведомления: {response.status_code} {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❗️Ошибка соединения: {e}")


    @staticmethod
    def send_tlg_message_close_tp_sl_order(order: Order) -> None:
        earn = DealsOrm.get_earn(order.order_id)
        #result_of_deal = ""
        # if order.avgPrice == "":
        #     result_of_deal = f"{PROJECT_NAME}\n🤝 Сделка {order.symbol} была отменена."
        # if order.status == "Sell":
        #     if float(order.basePrice) <= float(order.triggerPrice):
        #         result_of_deal = f"{PROJECT_NAME}\n🎉 Сделка {order.symbol} закрыта с прибылью!"
        #     elif float(order.basePrice) >= float(order.triggerPrice):
        #         result_of_deal = f"{PROJECT_NAME}\n😢 Сделка {order.symbol} закрыта с убытком..."
        # if order.status == "Buy":
        #     if float(order.basePrice) >= float(order.triggerPrice):
        #         result_of_deal = f"{PROJECT_NAME}\n🎉 Сделка {order.symbol} закрыта с прибылью!"
        #     elif float(order.basePrice) <= float(order.triggerPrice):
        #         result_of_deal = f"{PROJECT_NAME}\n😢 Сделка {order.symbol} закрыта с убытком..."

        message_title = (f"{PROJECT_NAME}\n"
                         f"💰 Результат для {order.symbol}: {earn} $\n")
        list_of_open_deals = DealsOrm.select_open_deals()
        count_open_limit_orders = len(list_of_open_deals)
        url = f"https://api.telegram.org/bot{TLG_TOKEN}/sendMessage"
        message = (f"{message_title}\n"
                   f"status: {order.status}\n"
                   f"side: {order.side}\n"
                   # f"tp: {order.take_profit}\n"
                   # f"sl: {order.stop_loss}\n"
                   f"qty: {order.qty}\n"
                   f"order_id: {order.order_id}\n"
                   f"price: {order.price}\n"
                   f"money_close: {round(float(order.money_close), 3)}\n"
                   f"tax_close: {round(float(order.tax_close), 3)}\n\n"
                   f"Открытых позиций: {count_open_limit_orders}"
                   )
        payload = {
            "chat_id": TLG_ADMIN_ID,
            "text": message
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("✉️ Уведомление о закрытии ордера успешно отправлено.")
            else:
                print(f"❗️Ошибка отправки уведомления: {response.status_code} {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❗️Ошибка соединения: {e}")