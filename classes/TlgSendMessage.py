from classes import SpotOrders
from settings import PROJECT_NAME
import requests
from config import TLG_TOKEN, TLG_ADMIN_ID

class TlgSendMessage:
    @staticmethod
    def send_tlg_message_new_tp_sl_order(spot: SpotOrders) -> None:
        message_title = f"{PROJECT_NAME}\n🔻 TP/SL ордер для {spot.symbol} успешно размещен\n"
        count_open_limit_orders = len(spot.list_of_deals)
        url = f"https://api.telegram.org/bot{TLG_TOKEN}/sendMessage"
        message = (f"{message_title}\n"
                   f"side: {spot.side_sell}\n"
                   f"tp: {spot.tp}\n"
                   f"sl: {spot.sl}\n"
                   f"order_id: {spot.order_id_sell}\n"
                   f"basePrice: {spot.basePrice}\n"
                   f"money: {round(float(spot.money_buy), 3)}\n"
                   f"status: {spot.status_sell}\n"
                   f"tax: {round(float(spot.tax_buy), 3)}\n\n"
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
    def send_tlg_message_close_tp_sl_order(spot: SpotOrders) -> None:
        result_of_deal = ""
        print(f"spot.close_price_sell {spot.close_price_sell} spot.basePrice {spot.basePrice} spot.triggerPrice {spot.triggerPrice}")
        if spot.close_price_sell == "":
            result_of_deal = f"{PROJECT_NAME}\n🤝 Сделка {spot.symbol} была отменена."
        elif float(spot.basePrice) <= float(spot.triggerPrice):
            result_of_deal = f"{PROJECT_NAME}\n🎉 Сделка {spot.symbol} закрыта с прибылью!"
        elif float(spot.basePrice) >= float(spot.triggerPrice):
            result_of_deal = f"{PROJECT_NAME}\n😢 Сделка {spot.symbol} закрыта с убытком..."

        #message_title = (f"{PROJECT_NAME}\n🎉 TP/SL ордер для {spot.symbol} закрыт. Сделка завершена!\n"
        message_title = (f"{result_of_deal}\n"
                         f"💰 Результат: {spot.earn} $\n")
        count_open_limit_orders = len(spot.list_of_deals) - 1
        url = f"https://api.telegram.org/bot{TLG_TOKEN}/sendMessage"
        message = (f"{message_title}\n"
                   f"side: {spot.side_sell}\n"
                   f"qty: {spot.qty}\n"
                   f"order_id: {spot.order_id_sell}\n"
                   f"close_price: {spot.close_price_sell}\n"
                   f"money: {round(float(spot.money_sell), 3)}\n"
                   f"status: {spot.status_sell}\n"
                   f"tax: {round(float(spot.tax_sell), 3)}\n\n"
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