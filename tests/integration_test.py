import time

import pytest
import random
from classes.SpotOrders import SpotOrders

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
         "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT",
         "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT",
         "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]

@pytest.fixture()
def spot() -> SpotOrders:
    random_coin = random.randint(0, len(COINS) - 1)
    spot = SpotOrders(COINS[random_coin])
    return spot

def test_open_and_cancel_tp_sl_order(spot):
    spot.limit_order_with_tp_sl(11,15,15)
    time.sleep(10)
    spot.get_info_about_limit_order()
    spot.get_info_about_tp_sl_order()
    # tp_sl_order = spot.find_tp_sl_order(spot.tp)
    # status = tp_sl_order['orderStatus']
    # if status == "Untriggered":
    order_id = spot.order_id_sell
    response = spot.cancel_order(order_id)
    assert f"Ордер {order_id} успешно отменен" == response