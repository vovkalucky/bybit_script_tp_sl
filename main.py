import time
from datetime import datetime, timedelta, timezone
from classes.TradeManager import TradeManager
from db.queries.orm import BaseOrm
from settings import DELAY, UTC_PLUS_TIMEZONE

if __name__ == "__main__":
    #create_logger()
    print("🔍 Запуск анализа сигналов...")
    BaseOrm.create_tables()
    #time.sleep(10)
    try:
        while True:
            current_time = datetime.now(timezone(timedelta(hours=UTC_PLUS_TIMEZONE)))
            print(f"⏱️ Старт анализа: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            trader = TradeManager()
            trader.find_and_execute_trade()
            print(f"💤 Ожидание {DELAY} секунд...\n")
            time.sleep(DELAY)
    except KeyboardInterrupt:
        print("🛑 Программа остановлена пользователем.")