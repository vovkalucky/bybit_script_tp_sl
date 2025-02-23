from typing import List

from tradingview_ta import TA_Handler, Interval
from classes.tech_analysis.TechAnalysis import TechAnalysis

COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT",
    "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT",
    "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT"
]


#TIMEFRAMES: List[str] = ['1h', '15m', '5m', '1m']

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
            #print(f"analysis {analysis}")
            RSI = analysis['COMPUTE']['RSI']
            STOCH_K = analysis['COMPUTE']['STOCH.K']
            CCI = analysis['COMPUTE']['CCI']
            ADX = analysis['COMPUTE']['ADX']
            AO = analysis['COMPUTE']['AO']
            MOM = analysis['COMPUTE']['Mom']
            MACD = analysis['COMPUTE']['MACD']
            STOCH_RSI = analysis['COMPUTE']['Stoch.RSI']
            WR = analysis['COMPUTE']['W%R']
            BBP = analysis['COMPUTE']['BBP']
            UO = analysis['COMPUTE']['UO']

            #print(f"{RSI} {STOCH_K} {CCI} {ADX} {AO} {MOM} {MACD} {STOCH_RSI} {WR} {BBP} {UO}")

            # if timeframe == "1h":
            #     REC = TechAnalysis.check_trend_by_atr(self.pair, "60")
            #     #REC = analysis["RECOMMENDATION"]
            #     print(f"{self.pair} {timeframe} REC: {REC}")
            #     #return REC in ["BUY","STRONG BUY"]
            #     return REC

            if timeframe == "15m":
                TREND = TechAnalysis.check_trend_by_atr(self.pair, "15")
                VOLUME = TechAnalysis.check_volumes(self.pair, "15", 14)
                oscilators_list = [RSI, WR, STOCH_RSI, MACD, BBP]
                BUY = oscilators_list.count("BUY")
                STRONG_BUY = oscilators_list.count("STRONG BUY")
                SELL = oscilators_list.count("SELL")
                STRONG_SELL = oscilators_list.count("STRONG SELL")
                REC = BUY + STRONG_BUY
                REC_SELL = SELL + STRONG_SELL
                print(f"{self.pair} {timeframe} REC: {REC} REC_SELL: {REC_SELL} VOLUME {VOLUME} TREND {TREND}")
                return REC >= 2 and REC_SELL <= 1 and VOLUME

            elif timeframe in ["5m", "1m"]:
                oscilators_list = [RSI, STOCH_K, MOM, ADX, AO]
                BUY = oscilators_list.count("BUY")
                STRONG_BUY = oscilators_list.count("STRONG BUY")
                SELL = oscilators_list.count("SELL")
                STRONG_SELL = oscilators_list.count("STRONG SELL")
                REC = BUY + STRONG_BUY
                REC_SELL = SELL + STRONG_SELL
                print(f"{self.pair} {timeframe} REC: {REC} REC_SELL: {REC_SELL}")
                return REC >= 2 and REC_SELL == 0
            return False


        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return False

    def has_trade_signal(self) -> bool:
        # if not self.analyze_with_indicators("1h"):
        #     return False
        if not self.analyze_with_indicators("15m"):
            return False

        # Проверяем младшие таймфреймы (5m и 1m) для подтверждения
        for tf_data in ["5m", "1m"]:
            if self.analyze_with_indicators(tf_data):
                return True  # Достаточно сигнала на одном из младших таймфреймов
        return False

#while True:
for coin in COINS:
    spot = AnalysisCoin(coin)
    signal = spot.has_trade_signal()
    print(f"RESULT: {signal}")
    break
