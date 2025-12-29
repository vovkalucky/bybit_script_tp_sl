from classes.tech_analysis.TechAnalysis import TechAnalysis

class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair

    def analyze_coin(self) -> str:
        try:
            timeframes = ['15', '60']

            for timeframe in timeframes:
                imbalance_bear = TechAnalysis.find_imbalance(
                    self.pair,
                    timeframe,
                    "bear",
                    limit=10,
                    imbalance=0.7,
                )

                if imbalance_bear:
                    print(f"[analyze_coin] Bear imbalance найден на {timeframe} для {self.pair}")
                    return "Buy"

            return "No signal"

        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair}: {e}")
            return "No signal"
