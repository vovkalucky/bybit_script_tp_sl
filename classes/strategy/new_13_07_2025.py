import ccxt
import time
import pandas as pd
from classes.tech_analysis.indicators import Indicators

# Настройки
EXCHANGE = ccxt.bybit()

# ==================== Основная логика ====================


class AnalysisCoin:
    last_signal_time = {}  # Для хранения времени последнего сигнала

    def __init__(self, pair):
        self.pair = pair

    def analyze_coin(self, timeframe, cooldown_minutes=60) -> str:
        try:
            now = time.time()
            last_time = self.last_signal_time.get(self.pair, 0)
            if now - last_time < cooldown_minutes * 60:
                return "No signal"

            ohlcv = EXCHANGE.fetch_ohlcv(self.pair, timeframe=timeframe, limit=240)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']

            ind = Indicators(df)
            ema200 = ind.ema('close', 200)
            rsi_val = ind.rsi('close', 14)
            macd_line, signal_line, hist = ind.macd('close')
            upper_bb, mid_bb, lower_bb = ind.bollinger_bands('close')
            adx_val = ind.adx(14)
            atr_val = ind.atr(14)

            # Последние значения
            c = close.iloc[-1]
            ema_now = ema200.iloc[-1]
            rsi_now = rsi_val.iloc[-1]
            hist_now = hist.iloc[-1]
            hist_prev = hist.iloc[-2]
            adx_now = adx_val.iloc[-1]
            bb_low = lower_bb.iloc[-1]
            atr_now = atr_val.iloc[-1]
            vol_now = volume.iloc[-1]

            # Дополнительно получаем данные 1h ТФ
            df_h1 = pd.DataFrame(EXCHANGE.fetch_ohlcv(self.pair, '1h', limit=200),
                                 columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            trend_h1 = Indicators(df_h1).ema('close', 100).iloc[-1]
            if c < trend_h1:
                return "No signal"  # 🔴 Отсев по глобальному тренду

            # Проверка импульса по текущей свечке
            range_now = df['high'].iloc[-1] - df['low'].iloc[-1]
            if range_now < atr_now * 1.2:
                return "No signal"  # 🔴 Слабый импульс

            # Breakout последних 20 свечей
            if c < df['high'].rolling(window=20).max().iloc[-2]:
                return "No signal"  # 🔴 Нет пробоя уровня

            # Объём выше среднего
            if vol_now < volume.rolling(20).mean().iloc[-1] * 1.5:
                return "No signal"  # 🔴 Объём недостаточный

            # Проверка паттерна (например, бычья свеча с длинным телом)
            body = abs(df['close'].iloc[-1] - df['open'].iloc[-1])
            shadow = df['high'].iloc[-1] - df['low'].iloc[-1]
            if body / shadow < 0.6:
                return "No signal"  # 🔴 Слишком много шума в свече

            if len(close) < 210:
                return "No signal"



            if any(pd.isna(x) for x in [ema_now, rsi_now, hist_now, hist_prev, adx_now, bb_low, atr_now]):
                return "No signal"

            # ⚠️ Фильтрация по волатильности
            if atr_now < 0.005 * c:
                return "No signal"

            # ⚠️ Проверка на достаточный объём
            avg_vol = volume.rolling(window=20).mean().iloc[-1]
            if vol_now < avg_vol * 0.8:
                return "No signal"

            # 🟢 Режим 1: тренд (усилен)
            price_above_ema = c > ema_now * 1.005  # выше на 0.5%
            strong_macd = hist_now > 0 and hist_now > hist_prev
            strong_rsi = rsi_now > 50
            in_trend = adx_now > 25 and price_above_ema and strong_macd and strong_rsi

            # 🟡 Режим 2: флэт (усилен)
            price_touching_bb = c <= bb_low * 1.01  # на уровне нижней полосы
            oversold_rsi = rsi_now < 30
            flat_macd = hist_now > hist_prev
            in_range = adx_now < 20 and price_touching_bb and oversold_rsi and flat_macd

            if in_trend or in_range:
                self.last_signal_time[self.pair] = now
                print(f"Buy {self.pair}!")
                return "Buy"

            return "No signal"

        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return "No signal"

# ==================== Тест запуска ====================

# COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT",
# "APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT",
# "ONDOUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]
#
# if __name__ == "__main__":
#     for coin in COINS:
#         spot = AnalysisCoin(coin)
#         result = spot.analyze_coin(timeframe="1h")
#         if result == "Buy":
#             print("✅ Сигнал LONG!")
#         else:
#             print("❌ Нет сигнала.")
