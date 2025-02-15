from typing import List
from tradingview_ta import TA_Handler, Interval
COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
        "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT",
        "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]
TIMEFRAMES: List[str] = [Interval.INTERVAL_1_HOUR, Interval.INTERVAL_15_MINUTES]

class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair

    def analyze_with_indicators(self, timeframe: str) -> bool:
        try:
            coin = TA_Handler(
                symbol=self.pair,
                screener="crypto",
                exchange="Bybit",
                interval=timeframe,
                timeout=7
            )
            analysis = coin.get_analysis().oscillators
            indicators = coin.get_analysis().indicators

            REC = indicators['Recommend.All']

            # if timeframe == "1d":
            #     CONDITIONS_1D = REC > 0.3
            #     print(f"{self.pair} {timeframe} REC: {REC}")
            #     return CONDITIONS_1D

            if timeframe == "1h":
                CONDITIONS_1H = REC > 0.6
                print(f"{self.pair} {timeframe} REC: {REC}")
                return CONDITIONS_1H


            elif timeframe in ["15m", "5m", "1m"]:
                CONDITIONS_1_5_15MIN = REC > 0.6
                print(f"{self.pair} {timeframe} REC: {REC}")
                return CONDITIONS_1_5_15MIN
            return False


        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return False

    def has_trade_signal(self) -> bool:

        # if not self.analyze_with_indicators("1d"):
        #     return False
        # Проверяем старший таймфрейм (15m) для определения тренда
        if not self.analyze_with_indicators("1h"):
            return False

        # Проверяем младшие таймфреймы (5m и 1m) для подтверждения
        for tf_data in ["15m", "5m", "1m"]:
            if self.analyze_with_indicators(tf_data):
                return True  # Достаточно сигнала на одном из младших таймфреймов
        return False

# for coin in COINS:
#     spot = AnalysisCoin(coin)
#     signal = spot.has_trade_signal()
#     print(f"RESULT: {signal}")
#     #break