import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

# Настройка биржи
EXCHANGE = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})


class AnalysisCoin:
    last_signal_time = {}

    def __init__(self, pair):
        self.pair = pair

    # --- ИНДИКАТОРЫ ---

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Стандартный RSI (Wilder's)"""
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)

        # Используем Com (center of mass) для соответствия EMA alpha=1/14
        ema_up = up.ewm(com=period - 1, adjust=False).mean()
        ema_down = down.ewm(com=period - 1, adjust=False).mean()

        rs = ema_up / ema_down
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.5) -> pd.DataFrame:
        """
        Увеличили std_dev до 2.5 для более точных входов без стоп-лосса.
        """
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        # Ширина канала в процентах (Bandwidth)
        bandwidth = (upper - lower) / sma
        return pd.DataFrame({'sma': sma, 'upper': upper, 'lower': lower, 'bandwidth': bandwidth})

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def to_df_from_ohlcv(ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df.sort_values('timestamp').reset_index(drop=True)

    # --- АНАЛИЗ ---
    def analyze_coin(self) -> str:
        """
        Стратегия: 'Elastic Snap'
        Таймфрейм входа: 5m
        Тренд: 15m/1h EMA
        Take Profit: 1% (гарантируется волатильностью канала)
        """
        try:
            # 1. Загрузка данных
            # M15 для определения тренда
            ohlcv_m15 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='15m', limit=200)
            # M5 для точного входа
            ohlcv_m5 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m', limit=100)

            if not ohlcv_m15 or not ohlcv_m5:
                return "No signal"

            df15 = self.to_df_from_ohlcv(ohlcv_m15)
            df5 = self.to_df_from_ohlcv(ohlcv_m5)

            if len(df15) < 50 or len(df5) < 50:
                return "No signal"

            # 2. Расчет индикаторов

            # --- Тренд (M15) ---
            ema200_m15 = self.calculate_ema(df15['close'], 200)

            # --- Точка входа (M5) ---
            # Используем отклонение 2.5 !!! Это фильтрует слабые сигналы.
            bb_m5 = self.calculate_bollinger(df5, period=20, std_dev=2.5)
            rsi_m5 = self.calculate_rsi(df5['close'], period=14)

            # 3. Анализ (Индекс -2 = последняя завершенная свеча, -1 = текущая)
            # Для безопасности берем данные закрытой свечи (-2),
            # но цену берем текущую (-1), чтобы понять, где мы прямо сейчас.

            idx_closed = -2
            idx_current = -1

            current_price = df5['close'].iloc[idx_current]

            # Данные по закрытой свече (M5)
            bb_lower_closed = bb_m5['lower'].iloc[idx_closed]
            bb_width_closed = bb_m5['bandwidth'].iloc[idx_closed]
            rsi_closed = rsi_m5.iloc[idx_closed]

            # Данные по тренду (M15) - берем последнюю закрытую
            trend_ema = ema200_m15.iloc[-1]
            price_m15 = df15['close'].iloc[-1]

            # --- УСЛОВИЯ ---

            # A. ГЛОБАЛЬНЫЙ ТРЕНД ИЛИ ФЛЭТ
            # Цена на M15 должна быть выше EMA200 (мы не ловим ножи на падающем рынке)
            # Либо RSI на M15 не должен быть перепродан (<30), чтобы не покупать на дне обвала
            is_uptrend = price_m15 > trend_ema

            # B. СИЛЬНАЯ ПЕРЕПРОДАННОСТЬ (M5)
            # RSI < 25 (более строго, чем 30) - значит паника
            is_oversold = rsi_closed < 28

            # C. ЦЕНА В ЗОНЕ ПОКУПКИ (M5)
            # Цена пробила или коснулась нижней линии Bollinger (2.5 std)
            # Проверяем и текущую цену, и закрытие предыдущей
            is_below_bb = (current_price <= bb_lower_closed) or (df5['close'].iloc[idx_closed] <= bb_lower_closed)

            # D. ФИЛЬТР ВОЛАТИЛЬНОСТИ (ВАЖНО ДЛЯ 1% TP)
            # Если ширина канала (Bandwidth) меньше 1.5% (0.015), то ловить там нечего,
            # цена просто ползет. Нам нужен всплеск.
            is_volatility_enough = bb_width_closed > 0.015

            # E. КУЛДАУН (Защита от спама)
            now = datetime.now(timezone.utc)
            last_ts = self.last_signal_time.get(self.pair)
            is_cooldown_passed = True
            if last_ts:
                seconds_passed = (now - last_ts).total_seconds()
                if seconds_passed < 3600:  # 60 минут пауза
                    is_cooldown_passed = False

            # --- ИТОГОВОЕ РЕШЕНИЕ ---
            if is_uptrend and is_oversold and is_below_bb and is_volatility_enough and is_cooldown_passed:
                self.last_signal_time[self.pair] = now

                print(f"\n💎 STRONG BUY SIGNAL: {self.pair} 💎")
                print(f"Price: {current_price} | BB Lower(2.5): {bb_lower_closed:.4f}")
                print(f"RSI: {rsi_closed:.2f} | Trend EMA200: {trend_ema:.4f}")
                print(f"Bandwidth: {bb_width_closed * 100:.2f}% (Target 1% possible)")

                return "Buy"

            return "No signal"

        except Exception as e:
            print(f"Error in analysis {self.pair}: {e}")
            return "No signal"

#--- ПРИМЕР ЗАПУСКА ---
# if __name__ == "__main__":
#     # Список основных пар (ликвидные монеты Bybit)
#     coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'DOGE/USDT']
#
#     print("Запуск сканера...")
#     for coin in coins:
#         analyzer = AnalysisCoin(coin)
#         signal = analyzer.analyze_coin()
#         print(signal)
#         if signal == "Buy":
#             # Здесь можно вызвать функцию отправки ордера
#             pass