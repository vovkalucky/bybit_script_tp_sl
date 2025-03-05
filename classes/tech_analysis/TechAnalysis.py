import time
from typing import List
import requests
from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY, BYBIT_SECRET_KEY
from settings import DEMO_TRADE

import time
from datetime import datetime, timedelta, timezone
from settings import UTC_PLUS_TIMEZONE


class TechAnalysis:
    session = HTTP(api_key=BYBIT_API_KEY,
                   api_secret=BYBIT_SECRET_KEY,
                   demo=DEMO_TRADE,
                   max_retries=10,
                   retry_delay=10)

    @classmethod
    def get_volume_from_klines(cls, symbol: str, interval: str, count: int) -> List[float]:
        klines = cls.session.get_kline(category="spot", symbol=symbol, interval=interval)
        volumes = klines['result']['list']
        volumes_list = []
        for volume in volumes[0:count]:
            volumes_list.append(float(volume[5]))
        volumes_list = volumes_list[::-1]
        return volumes_list

    @staticmethod
    def avg_volume(volumes_list: List[float]) -> float:
        return round(sum(volumes_list) / len(volumes_list), 3) if volumes_list else 0


    @staticmethod
    def check_volumes(coin: str, interval: str, count: int) -> bool:
        try:
            volumes_list = TechAnalysis.get_volume_from_klines(coin, interval, count)
            if not volumes_list:
                print(f"(check_volumes) Ошибка: пустой список объемов для {coin}")
                return False
            current_volume = float(volumes_list[-1])
            avg_volume = TechAnalysis.avg_volume(volumes_list)
            threshold = 1.2  # Допустим, сигнал дается при превышении на 20%
            print(f"(current_volume) {current_volume} (avg_volume) {avg_volume}")
            return current_volume > avg_volume * threshold
        except Exception as e:
            print(f"(check_volumes): {e}")


    @classmethod
    def get_klines(cls, symbol: str, interval: str, limit: int):
        klines = cls.session.get_kline(category="spot", symbol=symbol, interval=interval, limit=limit)
        reverse_klines = klines['result']['list'][::-1]
        return reverse_klines

    @classmethod
    def calculate_atr(cls, candles, period=14) -> float:
        """
        Рассчитывает Average True Range (ATR) для данного набора свечей.

        :param candles: Список свечей в формате [timestamp, open, high, low, close, ...]
        :param period: Период для расчета ATR (по умолчанию 14)
        :return: Значение ATR, округленное до 3 знаков
        """
        if len(candles) < period:
            raise ValueError("Недостаточно данных для расчета ATR")

        tr_values = []

        for i in range(1, len(candles)):
            high = float(candles[i][2])
            low = float(candles[i][3])
            close_prev = float(candles[i - 1][4])

            tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
            tr_values.append(tr)

        # Вычисляем ATR через SMA первых period значений
        atr = sum(tr_values[:period]) / period

        # Используем формулу экспоненциального сглаживания
        for i in range(period, len(tr_values)):
            atr = (atr * (period - 1) + tr_values[i]) / period

        return round(atr, 3)

    @classmethod
    def check_trend_by_atr(cls, symbol: str, interval:str, limit:int = 20) -> bool:
        klines = TechAnalysis.get_klines(symbol, interval, limit)
        atr = TechAnalysis.calculate_atr(klines)
        previous_close = float(klines[-2][4])
        close = float(klines[-1][4])
        #print(f"previous_close: {previous_close} close {close}")
        #print(f"atr {atr}")
        return close > (previous_close + atr)

    @classmethod
    def find_imbalance(cls, symbol: str, interval:str, limit: int = 10) -> bool:
        klines = TechAnalysis.get_klines(symbol, interval, limit)
        #print(f"(klines) {klines}")
        third_imb_kline = float(klines[-4][3]) #low
        second_imb_kline = float(klines[-3][3]) #low
        #second_imb_kline_body = round((float(klines[-3][1]) - float(klines[-3][4]))/float(klines[-3][1])*100, 6)
        first_imb_kline = float(klines[-2][2]) #high
        first_imb_kline_close = float(klines[-2][4]) #first_imb_kline close price
        current_kline = float(klines[-1][4]) #current_price
        print(f"third_imb_kline: {third_imb_kline} second_imb_kline: {second_imb_kline}"
              f" first_imb_kline: {first_imb_kline} first_imb_kline_close {first_imb_kline_close} current_kline: {current_kline}")

        condition_0 = second_imb_kline < third_imb_kline
        condition_1 = (first_imb_kline - current_kline)/first_imb_kline > 0.01 #для входа в сделку чтобы прибыль составила 1%
        condition_2 = (third_imb_kline - first_imb_kline)/third_imb_kline > 0.01 #размера тела падающей свечи более 1%


        list_of_conditions = [condition_0, condition_1, condition_2]
        print(f"(list_of_conditions) {symbol} {list_of_conditions}")
        if all(list_of_conditions):
            print(f"{symbol} 🥎🥎🥎🥎🥎🥎🥎 Imbalance find! 🥎🥎🥎🥎🥎🥎")
            return True



# coins = [
#     "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
#     "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT",
#     "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT",
#     "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT"
# ]
#
# while True:
#     current_time = datetime.now(timezone(timedelta(hours=UTC_PLUS_TIMEZONE)))
#     print(f"⏱️ Старт анализа: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
#     for coin in coins:
#         imb = TechAnalysis.find_imbalance(coin, "15", 10)
#         #break
#     time.sleep(300)


