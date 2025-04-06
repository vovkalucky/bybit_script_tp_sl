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
            imbalance_bull = TechAnalysis.find_imbalance(self.pair, timeframe, "bull", 10, 0.8, 1)
            imbalance_bear = TechAnalysis.find_imbalance(self.pair, timeframe,"bear", 10, 0.8, 1)
            print(f"[analyze_imbalance_and_trend] imbalance_bull {self.pair} {imbalance_bull}")
            print(f"[analyze_imbalance_and_trend] imbalance_bear {self.pair} {imbalance_bear}")
            if imbalance_bear == False or imbalance_bull == False:
                return "No signal"
            trend = TechAnalysis.determine_trend_ema(self.pair, "1h")
            print(f"[analyze_imbalance_and_trend] trend {self.pair} {trend}")

            if trend in ["Bull", "Flat"] and imbalance_bear:
                print(f"[analyze_imbalance_and_trend] Все условия для торговли выполнены {trend} {imbalance_bear}")
                return "Buy"
            elif trend in ["Bear", "Flat"] and imbalance_bull:
                print(f"[analyze_imbalance_and_trend] Все условия для торговли выполнены {trend} {imbalance_bull}")
                return "Sell"
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
