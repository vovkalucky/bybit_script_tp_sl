from typing import List
from tradingview_ta import TA_Handler, Interval

from classes.tech_analysis.TechAnalysis import TechAnalysis
#from settings import TIMEFRAMES

# COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
#         "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT",
#         "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]


#TIMEFRAMES: List[str] = ['1h', '15m', '5m']  # Обновленные таймфреймы


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
                timeout=10
            )
            analysis = coin.get_analysis()
            indicators = analysis.indicators
            close_price = indicators.get('close', 0)
            #print(f"close_price: {close_price}")

            if close_price == 0:
                return False

            EMA50 = indicators.get('EMA50')
            EMA200 = indicators.get('EMA200')
            ADX_PLUS_DI = indicators.get('ADX+DI')
            ADX_MINUS_DI = indicators.get('ADX-DI')

            # Общие условия для всех таймфреймов
            trend_condition = (
                    EMA50 > EMA200 and
                    ADX_PLUS_DI > ADX_MINUS_DI
            )

            if timeframe == "1h":
                ADX = indicators.get('ADX')
                RSI = indicators.get('RSI')
                MACD = indicators.get('MACD.macd')
                MACD_SIGNAL = indicators.get('MACD.signal')
                #print(f"{self.pair} 1h: Trend {trend_condition} ADX: {ADX} RSI: {RSI} MACD:{MACD} MACD_SIGNAL: {MACD_SIGNAL}")
                condition_1h = trend_condition and ADX > 25 and 50 < RSI < 70 and MACD > MACD_SIGNAL
                print(f"{self.pair} {timeframe} {condition_1h}")
                return condition_1h

            elif timeframe == "15m":
                #VOLUME = indicators.get('volume')
                CHECK_SMA20_VOLUME = TechAnalysis.check_volumes(self.pair, "15", 20)
                #SMA20 = indicators.get('SMA20')
                HULLMA9 = indicators.get('HullMA9')
                STOCH_K = indicators.get('Stoch.K')
                STOCH_D = indicators.get('Stoch.D')
                #print(f"{self.pair} 15m: Trend {trend_condition} {HULLMA9} {close_price} {STOCH_K} {STOCH_D} {CHECK_SMA20_VOLUME}")
                condition_15min = trend_condition and HULLMA9 < close_price and STOCH_K > STOCH_D and CHECK_SMA20_VOLUME
                print(f"{self.pair} {timeframe} {condition_15min}")
                return condition_15min

            # elif timeframe == "5m":
            #     #REC_BBPOWER = indicators.get('Rec.BBPower')
            #     EMA20 = indicators.get('EMA20')
            #     MACD = indicators.get('MACD.macd')
            #     #print(f"{self.pair} 5m: {REC_BBPOWER} {EMA20} {MACD}")
            #     return (
            #             #REC_BBPOWER == 1 and
            #             close_price > EMA20 and
            #             MACD > 0
            #     )
            # return False

        except Exception as e:
            print(f"⚠️ Ошибка анализа {self.pair} на {timeframe}: {e}")
            return False

    def has_trade_signal(self) -> bool:
        return all(self.analyze_with_indicators(tf) for tf in TIMEFRAMES)
        #return True
        #signals = []
        # for tf in TIMEFRAMES:
        #     result = self.analyze_with_indicators(tf)
        #     print(f"✅ {self.pair} {tf}: {result}")  # <- Проверка результата
        #     signals.append(result)
        # return all(signals)

# spot = AnalysisCoin("BNBUSDT")
# signal = spot.has_trade_signal()
# print(f"RESULT: {signal}")
# for coin in COINS:
#     spot = AnalysisCoin(coin)
#     signal = spot.has_trade_signal()
#     print(f"RESULT: {signal}")
#     break