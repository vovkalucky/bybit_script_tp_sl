import random
import pytest
import settings
from classes.SpotOrders import SpotOrders

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
         "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT",
         "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT",
         "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]

TIMEFRAMES_BYBIT = ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "M", "W"]
TIMEFRAMES_TV = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1W", "1M"]
RANDOM_COIN = COINS[random.randint(0, len(COINS) - 1)]
RANDOM_TIMEFRAME = random.choice(TIMEFRAMES_TV)


@pytest.fixture()
def spot() -> SpotOrders:
    settings.DEMO_TRADE = True
    random_coin = random.randint(0, len(COINS) - 1)
    spot = SpotOrders(COINS[random_coin])
    return spot