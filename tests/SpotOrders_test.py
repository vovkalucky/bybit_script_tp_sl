import pytest
import random
import requests
from classes.SpotOrders import SpotOrders

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
         "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT",
         "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT",
         "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]

@pytest.fixture()
def spot() -> SpotOrders:
    random_coin = random.randint(0, len(COINS) - 1)
    return SpotOrders(COINS[random_coin])

def test_limits(spot):
    price_decimals, qty_decimals, min_qty = spot.get_filters()
    assert type(price_decimals) == int
    assert type(qty_decimals) == int
    assert type(min_qty) == str
    print(price_decimals, qty_decimals, min_qty)

# def get_data(url):
#     response = requests.get(url)
#     return response.json()


# def test_get_order(mocker):
#     mock_get = mocker.patch("requests.get")  # Мокируем requests.get
#     mock_get.return_value.json.return_value = {"key": "value"}
#
#     result = get_data("https://example.com")
#     print(f"{result}")
#     assert result == {"key": "value"}
#     mock_get.assert_called_once_with("https://example.com")
