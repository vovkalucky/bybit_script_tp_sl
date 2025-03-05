from typing import List

from tradingview_ta import TA_Handler, Interval
from classes.tech_analysis.TechAnalysis import TechAnalysis

# COINS = [
#     "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
#     "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT",
#     "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT",
#     "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT"
# ]


#TIMEFRAMES: List[str] = ['1h', '15m', '5m', '1m']

class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair

    def analyze_with_indicators(self, timeframe: str) -> bool:
        try:
            return TechAnalysis.find_imbalance(self.pair, timeframe)

        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return False

    def has_trade_signal(self) -> bool:
        if self.analyze_with_indicators("15") or self.analyze_with_indicators("60"):
            return True
        else:
            return False

#while True:
# for coin in COINS:
#     spot = AnalysisCoin(coin)
#     signal = spot.has_trade_signal()
#     print(f"RESULT: {signal}")
#     break
