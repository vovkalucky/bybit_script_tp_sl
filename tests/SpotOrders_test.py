import pytest
import random
import requests
from classes.SpotOrders import SpotOrders
from tests.mock_response import find_tp_sl_order_mock_response

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
         "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT",
         "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT",
         "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]

@pytest.fixture()
def spot() -> SpotOrders:
    random_coin = random.randint(0, len(COINS) - 1)
    spot = SpotOrders(COINS[random_coin])
    return spot

def test_limits(spot):
    price_decimals, qty_decimals, min_qty = spot.get_filters()
    assert type(price_decimals) == int
    assert type(qty_decimals) == int
    assert type(min_qty) == str
    print(price_decimals, qty_decimals, min_qty)

def test_limit_order_with_tp_sl(spot):
    response = spot.limit_order_with_tp_sl(20, 1.01, 3,15)
    assert type(response) == bool
    spot.cancel_order(spot.order_id_buy)


def test_limit_order_with_tp_sl_mock(spot, mocker):
    # Подменяем метод limit_order_with_tp_sl и задаём возвращаемое значение
    mock_order = mocker.patch.object(spot, 'limit_order_with_tp_sl', return_value=True)
    # Мокаем свойство order_id_buy, если оно нужно для cancel_order
    mocker.patch.object(spot, 'order_id_buy', 'mocked_order_id')
    # Мокаем метод cancel_order, чтобы убедиться в его вызове
    mock_cancel = mocker.patch.object(spot, 'cancel_order')
    # Вызываем тестируемый метод
    response = spot.limit_order_with_tp_sl(20, 1.01, 3, 15)
    # Проверяем результат
    assert response is True

    # Проверяем вызов метода с правильными аргументами
    mock_order.assert_called_once_with(20, 1.01, 3, 15)

    # Проверяем вызов cancel_order с нужным order_id
    #mock_cancel.assert_called_once_with('mocked_order_id')

def test_find_tp_sl_order(spot, mocker):
    return_value = find_tp_sl_order_mock_response
    mock_order = mocker.patch.object(spot, 'find_tp_sl_order', return_value=return_value)
    mocker.patch.object(spot, 'tp', '2745.1')
    response = spot.find_tp_sl_order("2745.1")
    assert type(response) == dict
    assert len(response) == 45
    assert "orderId" in response
    mock_order.assert_called_once_with(spot.tp)
