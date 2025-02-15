from typing import List
from tradingview_ta import TA_Handler, Interval

from classes.tech_analysis.TechAnalysis import TechAnalysis
#from classes.tech_analysis.TechAnalysis import TechAnalysis
#from settings import TIMEFRAMES

COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT",
        "DOTUSDT", "LTCUSDT", "ATOMUSDT", "APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT",
        "TONUSDT", "SANDUSDT", "XLMUSDT", "HBARUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]


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

            if close_price == 0:
                return False

            # Общие индикаторы для всех таймфреймов
            EMA20 = indicators.get('EMA20')
            EMA50 = indicators.get('EMA50')
            ADX_PLUS_DI = indicators.get('ADX+DI')
            ADX_MINUS_DI = indicators.get('ADX-DI')
            VWMA = indicators.get('VWMA')
            CCI20 = indicators.get('CCI20')
            AO = indicators.get('AO')
            AO_prev = indicators.get('AO[1]')

            # Условие тренда (быстрее реагирует)
            trend_condition = (
                EMA20 > EMA50 and
                ADX_PLUS_DI > ADX_MINUS_DI
            )

            if timeframe == "1h":
                ADX = indicators.get('ADX')
                RSI = indicators.get('RSI')
                MACD = indicators.get('MACD.macd')
                MACD_SIGNAL = indicators.get('MACD.signal')
                AO_condition = AO > 0 and AO > AO_prev

                # Условия для 1h
                condition = (
                    trend_condition and
                    ADX > 20 and              # Сниженный порог силы тренда
                    55 < RSI < 65 and         # Ужесточенный диапазон RSI
                    MACD > MACD_SIGNAL and
                    AO_condition and
                    close_price > VWMA and    # Подтверждение объема
                    CCI20 > 50                # Умеренный импульс
                )
                print(f"{self.pair} {timeframe}: {condition}")
                return condition

            elif timeframe == "15m":
                HULLMA9 = indicators.get('HullMA9')
                STOCH_K = indicators.get('Stoch.K')
                STOCH_D = indicators.get('Stoch.D')
                BB_upper = indicators.get('BB.upper')
                CHECK_SMA20_VOLUME = TechAnalysis.check_volumes(self.pair, "15", 20)

                # Условия для 15m
                condition = (
                    trend_condition and
                    close_price > HULLMA9 and
                    STOCH_K > STOCH_D and
                    STOCH_K < 80 and          # Избегаем перекупленности
                    CHECK_SMA20_VOLUME and
                    close_price > indicators.get('Pivot.M.Classic.R1') and  # Уровни сопротивления
                    CCI20 > 100               # Сильный импульс
                )
                print(f"{self.pair} {timeframe}: {condition}")
                return condition

        except Exception as e:
            print(f"⚠️ Ошибка анализа {self.pair} на {timeframe}: {e}")
            return False

    def has_trade_signal(self) -> bool:
        return all(self.analyze_with_indicators(tf) for tf in ["1h", "15m"])


for coin in COINS:
    spot = AnalysisCoin(coin)
    signal = spot.has_trade_signal()
    print(f"RESULT: {signal}")
    #break