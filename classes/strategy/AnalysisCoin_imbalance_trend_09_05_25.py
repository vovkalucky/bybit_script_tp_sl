from classes.tech_analysis.TechAnalysis import TechAnalysis

class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair

    def analyze_imbalance_and_trend(self) -> str:
        timeframe = "15"
        try:
            imbalance_bear = TechAnalysis.find_imbalance(self.pair, timeframe,"bear", 10, 0.7, 0.8) #было 0.8 profit 0.9
            #print(f"[analyze_imbalance_and_trend] imbalance_bear {self.pair} {imbalance_bear}")
            if not imbalance_bear:
                return "No signal"
            #trend = TechAnalysis.detect_trend(self.pair, "15m")
            print(f"[analyze_imbalance_and_trend] trend {self.pair}")
            if imbalance_bear:
                print(f"[analyze_imbalance_and_trend] Все условия для торговли выполнены {imbalance_bear}")
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
