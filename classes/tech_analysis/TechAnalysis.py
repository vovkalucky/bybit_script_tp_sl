from http.client import responses
from typing import List
from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY, BYBIT_SECRET_KEY
from settings import DEMO_TRADE


class TechAnalysis:
    session = HTTP(api_key=BYBIT_API_KEY,
                   api_secret=BYBIT_SECRET_KEY,
                   demo=DEMO_TRADE,
                   max_retries=10,
                   retry_delay=10)

    @classmethod
    def get_volume_from_klines(cls, symbol: str, interval: str, count: int) -> List[float]:
        klines = cls.session.get_kline(category="spot", symbol=symbol, interval=interval)
        # print(klines)
        volumes = klines['result']['list']
        volumes_list = []
        for volume in volumes[0:count]:
            volumes_list.append(float(volume[5]))
        # print(volumes_list)
        volumes_list = volumes_list[::-1]
        #print(volumes_list)
        return volumes_list

    @staticmethod
    def avg_volume(volumes_list: List[float]) -> float:
        return round(sum(volumes_list) / len(volumes_list), 3) if volumes_list else 0


    @staticmethod
    def check_volumes(coin: str, interval: str, count: int) -> bool:
        try:
            volumes_list = TechAnalysis.get_volume_from_klines(coin, interval, count)
            if not volumes_list:
                return False
            current_volume = float(volumes_list[-2])
            avg_volume = TechAnalysis.avg_volume(volumes_list)
            if current_volume > avg_volume:
                return True
            else:
                return False
        except Exception as e:
            print(f"(check_volumes): {e}")

    @classmethod
    def count_atr(cls, symbol: str, interval: str, count: int):
        response_klines = cls.session.get_kline(category="spot", symbol=symbol, interval=interval)
        klines = response_klines['result']['list'][::-1]
        #print(klines)
        all_candles = []
        for i in klines:
            #Вычисляем длину свечи high - low
            all_candles.append(abs(round(float(i[2]) - float(i[3]), 3)))
        print(f"{len(all_candles)} {all_candles}")
        avg_candle = round(sum(all_candles)/len(all_candles), 3)
        print(f"(avg_candle) {avg_candle}")
        sorted_candles = []
        for candle in all_candles:
            # if candle > 2 * avg_candle:
            #     continue
            sorted_candles.append(candle)
        print(f"(sorted_candles) {len(sorted_candles)} {sorted_candles}")
        print(sorted_candles[-6:-1]) # 29.06, 29.73, 22.18, 34.73, 37.0
        atr = round(sum(sorted_candles[-6:-1])/5, 3)
        current_kline = sorted_candles[-1]
        print(f"atr {atr}")
        print(current_kline < atr)
        return current_kline < atr





atr = TechAnalysis.count_atr("ETHUSDT", "60", 20)


# sma20_volume = TechAnalysis.check_volumes("ETHUSDT", "60", 20)
# print(sma20_volume)