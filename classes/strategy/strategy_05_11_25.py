import ccxt
import time
import pandas as pd
from datetime import datetime, timezone
from classes.tech_analysis.indicators import Indicators

# Настройки
EXCHANGE = ccxt.bybit()
TIMEFRAME = '5m'  # Скальпинг на 5m: баланс между скоростью и шумом
LEV_RATE = 5  # Левередж для увеличения прибыли от мелких движений
RISK_PERCENT = 0.01  # Риск 1% на сделку
PROFIT_TARGET = 0.03  # Тейк-профит 0.3%
STOP_LOSS = 0.015  # Стоп-лосс 0.15%
MAX_POSITIONS = 10  # Макс. открытых позиций
PAIRS = ['BTC/USDT', 'ETH/USDT']  # Ликвидные пары для скальпинга

# ==================== Основная логика ====================

class AnalysisCoin:
    last_signal_time = {}  # Для хранения времени последнего сигнала

    def __init__(self, pair):
        self.pair = pair

    def analyze_coin(self, timeframe) -> str:
        try:
            ohlcv = EXCHANGE.fetch_ohlcv(self.pair, timeframe=timeframe, limit=50)  # Меньше данных для скорости
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            close = df['close']
            high = df['high']
            low = df['low']
            volume = df['volume']

            # Короткосрочные индикаторы для скальпинга
            ind = Indicators(df)
            ema20 = ind.ema('close', 20)  # Быстрая EMA вместо 200
            rsi_val = ind.rsi('close', 14)
            macd_line, signal_line, hist = ind.macd('close')
            upper_bb, mid_bb, lower_bb = ind.bollinger_bands('close')
            adx_val = ind.adx(14)
            atr_val = ind.atr(14)

            # Последние значения
            c = close.iloc[-1]
            ema_now = ema20.iloc[-1]
            rsi_now = rsi_val.iloc[-1]
            hist_now = hist.iloc[-1]
            hist_prev = hist.iloc[-2]
            adx_now = adx_val.iloc[-1]
            bb_low = lower_bb.iloc[-1]
            atr_now = atr_val.iloc[-1]
            vol_now = volume.iloc[-1]

            # Тренд по 1h (глобальный)
            df_h1 = pd.DataFrame(EXCHANGE.fetch_ohlcv(self.pair, '1h', limit=200),
                                 columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            trend_h1 = Indicators(df_h1).ema('close', 100).iloc[-1]
            if c < trend_h1:
                print(f"{self.pair} Отсев по глобальному тренду")
                return "No signal"  # 🔴 Отсев по глобальному тренду

            # Волатильность для скальпинга
            if atr_now < 0.005 * c:
                print(f"{self.pair} Слишком низкая волатильность")
                return "No signal"  # 🔴 Слишком низкая волатильность

            # Объём выше среднего (для подтверждения импульса)
            if vol_now < volume.rolling(10).mean().iloc[-1] * 1.2:
                print(f"{self.pair} Недостаточный объём")
                return "No signal"  # 🔴 Недостаточный объём

            # Паттерн свечи: Бычья (для BUY) или Медвежья (для SELL)
            body = abs(close.iloc[-1] - df['open'].iloc[-1])
            shadow = high.iloc[-1] - low.iloc[-1]
            if body / shadow < 0.5:  # Слишком много шума
                return "No signal"

            if len(close) < 25 or any(pd.isna(x) for x in [ema_now, rsi_now, hist_now, hist_prev, adx_now, bb_low, atr_now]):
                return "No signal"

            # Режим BUY: Отскок в тренде вверх
            price_above_ema = c > ema_now * 1.002  # Легко выше EMA
            bullish_rsi = rsi_now < 35 and rsi_now > rsi_val.iloc[-2]  # Оверсолд с ростом
            bullish_macd = hist_now > hist_prev and hist_now > 0
            buy_signal = adx_now > 20 and price_above_ema and bullish_rsi and bullish_macd

            # Режим SELL: Аналог для shorts (если рынок поддерживает)
            price_below_ema = c < ema_now * 0.998
            bearish_rsi = rsi_now > 65 and rsi_now < rsi_val.iloc[-2]
            bearish_macd = hist_now < hist_prev and hist_now < 0
            sell_signal = adx_now > 20 and price_below_ema and bearish_rsi and bearish_macd

            if buy_signal:
                print("Buy")
                return "Buy"
            elif sell_signal:
                print("Sell")
                return "Sell"
            else:
                print("No signal")
                return "No signal"

        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return "No signal"

# if __name__ == "__main__":
for coin in PAIRS:
    spot = AnalysisCoin(coin)
    result = spot.analyze_coin(timeframe="5m")
# class ScalpingStrategy:
#     def __init__(self):
#         self.open_positions = {}  # Хранение открытых позиций: {pair: {'type': 'buy/sell', 'entry_price':, 'tp':, 'sl':, 'time':}}
#
#     def run(self):
#         while True:
#             for pair in PAIRS:
#                 if len(self.open_positions) >= MAX_POSITIONS:
#                     break  # Ограничение позиций
#
#                 analyzer = AnalysisCoin(pair)
#                 signal = analyzer.analyze_coin(TIMEFRAME)
#
#                 if signal in ["Buy", "Sell"]:
#                     balance = EXCHANGE.fetch_balance()['USDT']['free']
#                     risk_amount = balance * RISK_PERCENT
#
#                     # Получаем текущую цену
#                     ticker = EXCHANGE.fetch_ticker(pair)
#                     current_price = ticker['last']
#
#                     if signal == "Buy":
#                         entry_price = current_price
#                         sl_price = entry_price * (1 - STOP_LOSS)
#                         tp_price = entry_price * (1 + PROFIT_TARGET)
#                         size = (risk_amount / (entry_price - sl_price)) / LEV_RATE  # Размер с учётом риска и левереджа
#                         self.open_positions[pair] = {'type': 'buy', 'entry_price': entry_price, 'tp': tp_price, 'sl': sl_price, 'size': size, 'time': time.time()}
#                         print(f"📈 BUY {pair}: Entry={entry_price}, SL={sl_price}, TP={tp_price}, Size={size}")
#                         # EXCHANGE.create_market_buy_order(pair, size, lever=LEV_RATE)  # Раскомментировать для реальной торговли
#                     elif signal == "Sell":
#                         entry_price = current_price
#                         sl_price = entry_price * (1 + STOP_LOSS)
#                         tp_price = entry_price * (1 - PROFIT_TARGET)
#                         size = (risk_amount / (sl_price - entry_price)) / LEV_RATE
#                         self.open_positions[pair] = {'type': 'sell', 'entry_price': entry_price, 'tp': tp_price, 'sl': sl_price, 'size': size, 'time': time.time()}
#                         print(f"📉 SELL {pair}: Entry={entry_price}, SL={sl_price}, TP={tp_price}, Size={size}")
#                         # EXCHANGE.create_market_sell_order(pair, size, lever=LEV_RATE)  # Раскомментировать
#
#             # Проверка открытых позиций для выхода
#             to_close = []
#             for pair, pos in self.open_positions.items():
#                 ticker = EXCHANGE.fetch_ticker(pair)
#                 current_price = ticker['last']
#                 if pos['type'] == 'buy':
#                     if current_price >= pos['tp'] or current_price <= pos['sl'] or (time.time() - pos['time']) > 600:  # TP/SL или 10 мин
#                         print(f"🚪 CLOSE BUY {pair}: Price={current_price}, P&L={(current_price - pos['entry_price'])/pos['entry_price']:.2%}")
#                         # EXCHANGE.create_market_sell_order(pair, pos['size'])  # Закрыть
#                         to_close.append(pair)
#                 elif pos['type'] == 'sell':
#                     if current_price <= pos['tp'] or current_price >= pos['sl'] or (time.time() - pos['time']) > 600:
#                         print(f"🚪 CLOSE SELL {pair}: Price={current_price}, P&L={(pos['entry_price'] - current_price)/pos['entry_price']:.2%}")
#                         # EXCHANGE.create_market_buy_order(pair, pos['size'])  # Закрыть
#                         to_close.append(pair)
#             for pair in to_close:
#                 del self.open_positions[pair]
#
#             time.sleep(10)  # Проверка каждые 10 сек (для 5m TF)