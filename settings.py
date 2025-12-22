PROJECT_NAME = "#bybit_demo_trade_22_12_25"
TABLE_DEALS = "bybit_test_deals"
TABLE_COINS = "bybit_test_coins"

DELAY = 120
MAX_COUNT_OF_DEALS = 4
MONEY_FOR_ONE_ORDER = 100
TAKE_PROFIT = 0.8 #1
STOP_LOSS = 0.8 #1
TAKER_FEE = 0.001      # 0.1% комиссия Bybit
SLIPPAGE = 0.0003     # 0.03% запас под проскальзывание SL
DEMO_TRADE = True
DROP_TABLES = True
# Задержка между сделками для одной монеты (в часах)
COIN_COOLDOWN_HOURS = 24  #16
# Максимальное количество одновременных сделок по одной монете
MAX_DEALS_PER_COIN = 3 #5
# COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT",
# "APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT",
# "ONDOUSDT", "MNTUSDT", "TRXUSDT", "DOGSUSDT", "TWTUSDT", "ASTERUSDT"]
COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "TWTUSDT", "ASTERUSDT", "LINKUSDT"]
