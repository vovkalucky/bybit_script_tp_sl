import time
from datetime import datetime
from classes.TradeManager import TradeManager
from db.queries.orm import BaseOrm
from settings import DELAY

if __name__ == "__main__":
    print("🔍 Запуск анализа сигналов...")
    BaseOrm.create_tables()
    time.sleep(10)
    try:
        while True:
            current_time = datetime.now()
            print(f"⏱️ Старт анализа: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            trader = TradeManager()
            trader.find_and_execute_trade()
            print(f"💤 Ожидание {DELAY} секунд...\n")
            time.sleep(DELAY)
    except KeyboardInterrupt:
        print("🛑 Программа остановлена пользователем.")