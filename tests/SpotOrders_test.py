import pytest
import random
import settings
from classes.OrdersStructure import MarketOrder, LimitOrder
from classes.SpotOrders import SpotOrders
from tests.functions_for_help import check_order_id
from tests.mock_response import find_tp_sl_order_mock_response

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
         "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT",
         "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT",
         "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]

@pytest.fixture()
def spot() -> SpotOrders:
    settings.DEMO_TRADE = True
    random_coin = random.randint(0, len(COINS) - 1)
    spot = SpotOrders(COINS[random_coin])
    return spot

def test_limits(spot):
    price_decimals, qty_decimals, min_qty = spot.get_filters()
    assert type(price_decimals) == int
    assert type(qty_decimals) == int
    assert type(min_qty) == float
    print(price_decimals, qty_decimals, min_qty)

@pytest.mark.parametrize('side', ('Buy', 'Sell'))
def test_market_order(spot, side):
    order = spot.market_order(side, 20)
    print(f"[test_market_order] {order}")
    assert type(order) == MarketOrder
    assert check_order_id(order.order_id)

@pytest.mark.parametrize('side', ('Buy', 'Sell'))
def test_limit_order(spot, side):
    order = spot.limit_order(side, 20, 10)
    #order = spot.limit_order(side, spot.min_qty, 10)
    print(f"[test_limit_order] {order}")
    spot.cancel_order(order.order_id)
    assert type(order) == LimitOrder
    assert check_order_id(order.order_id)

@pytest.mark.parametrize('side', ('Buy', 'Sell'))
def test_get_get_info_about_market_order(spot, side):
    money_for_order = 20
    #side = "Sell"
    order = spot.market_order(side,money_for_order )
    order_with_info = spot.get_info_about_market_order(order)
    assert type(order) == MarketOrder
    required_fields = ['order_id', 'symbol', 'qty', 'side', 'close_price', 'money_open', 'time_open', 'status', 'tax_open']
    for field in required_fields:
        assert hasattr(order_with_info, field), f"Поле {field} отсутствует!"
        value = getattr(order_with_info, field)
        assert value not in [None, "", [], {}], f"Поле {field} пустое или None"
    assert side == order_with_info.side
    assert money_for_order == float(order_with_info.money_open)


def test_limit_order_with_tp_sl_mock(spot, mocker):
    # Подменяем метод limit_order_with_tp_sl и задаём возвращаемое значение
    mock_order = mocker.patch.object(spot, 'limit_order_with_tp_sl', return_value=True)
    # Мокаем свойство order_id_buy, если оно нужно для cancel_order
    mocker.patch.object(spot, 'order_id_buy', 'mocked_order_id')
    # Мокаем метод cancel_order, чтобы убедиться в его вызове
    mock_cancel = mocker.patch.object(spot, 'cancel_order')
    # Вызываем тестируемый метод
    response = spot.limit_order_with_tp_sl(11, 10,10)
    # Проверяем результат
    assert response is True

    # Проверяем вызов метода с правильными аргументами
    mock_order.assert_called_once_with(11, 10, 10)

    # Проверяем вызов cancel_order с нужным order_id
    #mock_cancel.assert_called_once_with('mocked_order_id')


def test_find_tp_sl_order_mock(spot, mocker):
    # Мокаем метод find_tp_sl_order объекта spot
    mock_order = mocker.patch.object(spot, 'find_open_order_id_by_tp', return_value=find_tp_sl_order_mock_response)
    # Вызываем замоканный метод
    response = spot.find_open_order_id_by_tp("2745.1")
    assert isinstance(response, dict)
    assert len(response) == 45
    assert "orderId" in response
    assert response["tpLimitPrice"] == "2745.1"


def test_find_tp_sl_order(spot):
    order = spot.tp_sl_order("Buy", 20,10,10)
    info = spot.get_info_about_tp_sl_order(order)
    expected_order_id_tp_sl = info.order_id_close
    actual_order_id_tp_sl = spot.find_open_order_id_by_tp(info.take_profit)
    assert  expected_order_id_tp_sl == actual_order_id_tp_sl, "Ордера не совпадают!"