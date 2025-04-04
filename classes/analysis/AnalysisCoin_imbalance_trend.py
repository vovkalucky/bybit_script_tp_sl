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

    def analyze_imbalance_and_trend(self) -> str:
        timeframe = "15"
        try:
            #imbalance = TechAnalysis.find_bull_imbalance(self.pair, timeframe, 10, 0.5, 0.8)
            imbalance_bull = TechAnalysis.find_imbalance(self.pair, timeframe, "bull", 10, 0.6, 0.8)
            imbalance_bear = TechAnalysis.find_imbalance(self.pair, timeframe,"bear", 10, 0.6, 0.8)
            print(f"[analyze_imbalance_and_trend] {self.pair} {imbalance_bull}")
            print(f"[analyze_imbalance_and_trend] {self.pair} {imbalance_bear}")
            trend = TechAnalysis.determine_trend_ema(self.pair, "1h")
            print(f"[analyze_imbalance_and_trend] {self.pair} {trend}")
            if trend in ["Bear", "Flat", "Bull"] and imbalance_bear == "Sell":
                return "Sell"
            elif trend in ["Bull", "Flat", "Bear"] and imbalance_bull == "Buy":
                return "Buy"
            else:
                return "No signal"
        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return "No signal"

#while True:
# for coin in COINS:
#     spot = AnalysisCoin(coin)
#     signal = spot.has_trade_signal()
#     print(f"RESULT: {signal}")
#     break
