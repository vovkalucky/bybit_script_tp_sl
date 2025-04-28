import random
import settings
import pytest
from classes.SpotOrders import SpotOrders
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB


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

# @pytest.fixture(scope='function')
# def db_session():
#     # Создаём тестовую БД на лету
#     test_db_url = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5433/test_{POSTGRES_DB}"
#     engine = create_engine(test_db_url)
#
#     # Создание всех таблиц (если нужно)
#     # from models import Base
#     # Base.metadata.create_all(engine)
#
#     Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#     session = Session()
#
#     yield session  # передаем сессию в тест
#
#     session.close()  # после теста закрываем сессию
#
#     # Удаляем таблицы (если нужно)
#     # Base.metadata.drop_all(engine)