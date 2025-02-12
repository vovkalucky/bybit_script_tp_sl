import os
from dotenv import load_dotenv
load_dotenv()  # Загружаем переменные из файла .env

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_SECRET_KEY = os.getenv("BYBIT_SECRET_KEY")
TLG_TOKEN = os.getenv("TLG_TOKEN")
TLG_ADMIN_ID = os.getenv("TLG_ADMIN_ID")