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

    # def analyze_with_indicators_buy(self, timeframe: str) -> bool:
    #     try:
    #         imbalance = TechAnalysis.find_bear_imbalance(self.pair, timeframe, 10,0.5, 0.8)
    #         trend = TechAnalysis.determine_trend_ema(self.pair, "1h")
    #         return trend in ["Bull", "Flat"] and imbalance == "Buy"
    #     except Exception as e:
    #         print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
    #         return False
    #
    #
    # def analyze_with_indicators_sell(self, timeframe: str) -> bool:
    #     try:
    #         imbalance = TechAnalysis.find_bull_imbalance(self.pair, timeframe, 10, 0.5, 0.8)
    #         trend = TechAnalysis.determine_trend_ema(self.pair, "1h")
    #         return trend in ["Bear", "Flat"] and imbalance == "Sell"
    #     except Exception as e:
    #         print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
    #         return False

    def analyze_imbalance_and_trend(self) -> str:
        timeframe = "15"
        try:
            #imbalance = TechAnalysis.find_bull_imbalance(self.pair, timeframe, 10, 0.5, 0.8)
            imbalance_bull = TechAnalysis.find_imbalance(self.pair, timeframe, "bull", 10, 0.6, 0.8)
            imbalance_bear = TechAnalysis.find_imbalance(self.pair, timeframe,"bear", 10, 0.6, 0.8)
            trend = TechAnalysis.determine_trend_ema(self.pair, "1h")
            if trend in ["Bear"] and imbalance_bear == "Sell":
                return "Sell"
            elif trend in ["Bull"] and imbalance_bull == "Buy":
                return "Buy"
            else:
                return "No signal"
        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return "No signal"

    # def has_trade_signal(self) -> str:
    #     if self.analyze_with_indicators("15") == "Sell":
    #         return "Sell"
    #     elif self.analyze_with_indicators("15") == "Buy":
    #         return "Buy"
    #     else:
    #         return "No signal"

    # def has_trade_signal_buy(self) -> bool:
    #     if self.analyze_with_indicators_buy("15"): #or self.analyze_with_indicators("60")
    #         return True
    #     else:
    #         return False
    #
    # def has_trade_signal_sell(self) -> bool:
    #     if self.analyze_with_indicators_sell("15"): #or self.analyze_with_indicators("60")
    #         return True
    #     else:
    #         return False

#while True:
# for coin in COINS:
#     spot = AnalysisCoin(coin)
#     signal = spot.has_trade_signal()
#     print(f"RESULT: {signal}")
#     break
