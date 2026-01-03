# import allure
# from classes.OrdersStructure import Order
# from classes.TlgSendMessage import TlgSendMessage
#
#
# class TestTlgSendMessage:
#     @allure.title("test_send_tlg_message_new_tp_sl_order")
#     @allure.description("Тест функции отправки уведомления в Телеграм")
#     def test_send_tlg_message_new_tp_sl_order(self):
#         order = Order(order_id='orderId', symbol='BTCUSDT', qty_open='cumExecQty',
#                       side_open='side', status='status_tp_sl_order', avgPrice='avgPrice',
#                       money_open='222', tax_open='11', time_open='createdTime',
#                       price='price', take_profit='takeProfit', stop_loss='stopLoss',
#                       order_id_close='1212444', money_close="0", tax_close="0"
#                       )
#         fact_result = "✉️ Уведомление об установке ордера успешно отправлено."
#         actual_result = TlgSendMessage.send_tlg_message_new_tp_sl_order(order)
#         print(actual_result)
#         assert fact_result == actual_result, "Тест на отправку уведомления в Телеграм не выполнен"