import ccxt
import pandas as pd
from classes.tech_analysis.indicators import Indicators

# Настройки
EXCHANGE = ccxt.bybit()

# ==================== Основная логика ====================

class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair

    def analyze_coin(self, timeframe) -> str:
        try:
            ohlcv = EXCHANGE.fetch_ohlcv(self.pair, timeframe=timeframe, limit=240)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            close = df['close']
            high = df['high']
            low = df['low']

            if len(close) < 210:
                #print(f"{self.pair}: Недостаточно данных.")
                return "No signal"

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

            if any(pd.isna(x) for x in [ema_now, rsi_now, hist_now, hist_prev, adx_now, bb_low, atr_now]):
                #print(f"{self.pair}: Есть NaN в индикаторах.")
                return "No signal"

            # ⚠️ Проверка на волатильность
            if atr_now < 0.005 * c:
                #print(f"⚠️ Волатильность низкая (ATR={atr_now:.2f}) — сигнал отклонён.")
                return False

            # 🟢 Режим 1: тренд
            in_trend = adx_now > 25 and c > ema_now and hist_prev < hist_now and hist_now > 0 and rsi_now > 40

            # 🟡 Режим 2: флэт
            in_range = adx_now < 20 and c <= bb_low and rsi_now < 30 and hist_now > hist_prev

            if in_trend or in_range:
                print(f"Buy {self.pair}!")
                return "Buy"
            else:
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
#         result = spot.analyze(timeframe="1h", limit=250)
#         if result == "Buy":
#             print("✅ Сигнал LONG!")
#         else:
#             print("❌ Нет сигнала.")

