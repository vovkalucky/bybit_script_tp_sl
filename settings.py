from typing import List
from tradingview_ta import Interval
PROJECT_NAME = "#bybit_tp_sl_11_02_25"

TIMEFRAMES: List[str] = [Interval.INTERVAL_1_HOUR, Interval.INTERVAL_15_MINUTES]


UTC_PLUS_TIMEZONE = 3 #определяем добавку в часах для UTC
DELAY = 60 #задержка между запросами к tradingview
MAX_COUNT_OF_DEALS = 1
MONEY_FOR_ONE_ORDER = 50
PERCENT_OF_EARN = 1.01
STOP_LOSS = 0.98
DEMO_TRADE = True
STATE_FILE = "classes/list_of_deals.json"
CSV_FILE = "classes/money.csv"
COINS_LIST = "classes/coins.json"
