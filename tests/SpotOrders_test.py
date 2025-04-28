import pytest
from classes.OrdersStructure import Order
from tests.functions_for_help import check_order_id
from tests.mock_response import find_tp_sl_order_mock_response


class TestSpotOrders:
    def test_limits(self, spot):
        price_decimals, qty_decimals, min_qty = spot.get_filters()
        assert type(price_decimals) == int
        assert type(qty_decimals) == int
        assert type(min_qty) == float
        #print(price_decimals, qty_decimals, min_qty)


    def test_get_current_price_of_coin(self, spot):
        price = spot.get_current_price_of_coin()
        assert type(price) == float, "[test_get_current_price_of_coin] Ошибка типа данных!"


    @pytest.mark.parametrize('side', ('Buy', 'Sell'))
    def test_market_order(self, spot, side):
        order = spot.market_order(side, 7)
        print(f"[test_market_order] {order}")
        assert type(order) == Order
        assert check_order_id(order.order_id)

    @pytest.mark.parametrize('side', ('Buy', 'Sell'))
    def test_limit_order(self, spot, side):
        order = spot.limit_order(side, 7, 10)
        print(f"[test_limit_order] {order}")
        spot.cancel_order(order.order_id)
        assert type(order) == Order
        assert check_order_id(order.order_id)

    # @pytest.mark.parametrize('side', ('Buy', 'Sell'))
    # def test_get_info_about_market_order(spot, side):
    #     money_for_order = 20
    #     #side = "Sell"
    #     order = spot.market_order(side,money_for_order )
    #     order_with_info = spot.get_info_about_market_order(order)
    #     assert type(order) == Order
    #     required_fields = ['order_id', 'symbol', 'qty', 'side', 'close_price', 'money_open', 'time_open', 'status', 'tax_open']
    #     for field in required_fields:
    #         assert hasattr(order_with_info, field), f"Поле {field} отсутствует!"
    #         value = getattr(order_with_info, field)
    #         assert value not in [None, "", [], {}], f"Поле {field} пустое или None"
    #     assert side == order_with_info.side
    #     assert money_for_order == float(order_with_info.money_open)


    def test_tp_sl_order_mock(self, spot, mocker):
        # Мокаем метод tp_sl_order
        mock_order = mocker.patch.object(spot, 'tp_sl_order',
                                         return_value=Order(order_id="1912086819131100417", status="Filled"))

        # Вызываем метод
        response = spot.tp_sl_order("Buy", 7, 10, 10)

        # Проверяем, что tp_sl_order был вызван с нужными аргументами
        mock_order.assert_called_once_with("Buy", 7, 10, 10)

        # Проверяем тип возвращаемого объекта
        assert isinstance(response, Order)

        # Проверяем конкретные поля объекта (если нужно)
        assert response.order_id == "1912086819131100417"
        assert response.status == "Filled"


    def test_find_tp_sl_order_mock(self, spot, mocker):
        # Мокаем метод find_tp_sl_order объекта spot
        mock_order = mocker.patch.object(spot, 'find_open_order_id_by_tp', return_value=find_tp_sl_order_mock_response)
        # Вызываем замоканный метод
        response = spot.find_open_order_id_by_tp("2745.1")
        assert isinstance(response, dict)
        assert len(response) == 45
        assert "orderId" in response
        assert response["tpLimitPrice"] == "2745.1"


    def test_find_tp_sl_order(self, spot):
        order = spot.tp_sl_order("Buy", 6,10,10)
        info = spot.get_info_about_tp_sl_order(order)
        expected_order_id_tp_sl = info.order_id_close
        actual_order_id_tp_sl = spot.find_open_order_id_by_tp(info.take_profit)
        assert  expected_order_id_tp_sl == actual_order_id_tp_sl, "Ордера не совпадают!"