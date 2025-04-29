import os
from dotenv import load_dotenv
from settings import DEMO_TRADE


load_dotenv()  # Загружаем переменные из файла .env

TLG_TOKEN = os.getenv("TLG_TOKEN")
TLG_ADMIN_ID = os.getenv("TLG_ADMIN_ID")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
MODE = os.getenv("MODE")

def get_config():
    if DEMO_TRADE:
        return {
            "api_key": os.getenv("BYBIT_DEMO_API_KEY"),
            "api_secret": os.getenv("BYBIT_DEMO_SECRET_KEY"),
            "demo": True,
            "POSTGRES_DB": os.getenv("POSTGRES_DB_TEST")
        }
    else:
        return {
            "api_key": os.getenv("BYBIT_API_KEY"),
            "api_secret": os.getenv("BYBIT_SECRET_KEY"),
            "demo": False,
            "POSTGRES_DB": os.getenv("POSTGRES_DB")
        }

