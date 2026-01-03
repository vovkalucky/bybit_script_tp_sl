import ccxt
import pandas as pd
# import numpy as np
# from datetime import datetime, timezone

# Настройка биржи
EXCHANGE = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})


class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair

    # ----------------------- Индикаторы -----------------------
    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ema_up = up.ewm(com=period - 1, adjust=False).mean()
        ema_down = down.ewm(com=period - 1, adjust=False).mean()
        rs = ema_up / ema_down
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        bandwidth = (upper - lower) / sma
        return pd.DataFrame({'sma': sma, 'upper': upper, 'lower': lower, 'bandwidth': bandwidth})

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
        return df['volume'].rolling(period).mean()

    @staticmethod
    def to_df_from_ohlcv(ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        return df.sort_values('timestamp').reset_index(drop=True)

    def analyze_coin(self, debug=False) -> str:
        """
        Многоуровневая скальпинг-стратегия:
        3 паттерна входа для увеличения частоты сигналов
        """
        try:
            # Получаем данные только на рабочем таймфрейме (5m) + старший (1h для фильтра)
            ohlcv_1h = EXCHANGE.fetch_ohlcv(self.pair, timeframe='1h', limit=50)
            ohlcv_5m = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m', limit=100)

            if not ohlcv_1h or not ohlcv_5m:
                return "No signal"

            df_1h = self.to_df_from_ohlcv(ohlcv_1h)
            df = self.to_df_from_ohlcv(ohlcv_5m)

            if len(df) < 50 or len(df_1h) < 20:
                return "No signal"

            # Индикаторы
            ema9 = self.calculate_ema(df['close'], 9)
            ema21 = self.calculate_ema(df['close'], 21)
            ema50_1h = self.calculate_ema(df_1h['close'], 50)
            bb = self.calculate_bollinger(df, period=20, std_dev=2.0)
            rsi = self.calculate_rsi(df['close'], 14)
            vol_sma = self.calculate_volume_sma(df, 20)

            # Текущие и предыдущие значения (используем -2 для закрытой свечи)
            idx = -2
            close = df['close'].iloc[idx]
            close_prev = df['close'].iloc[idx - 1]
            ema9_curr = ema9.iloc[idx]
            ema9_prev = ema9.iloc[idx - 1]
            ema21_curr = ema21.iloc[idx]
            ema21_prev = ema21.iloc[idx - 1]
            bb_lower = bb['lower'].iloc[idx]
            bb_upper = bb['upper'].iloc[idx]
            bb_middle = bb['sma'].iloc[idx]
            rsi_curr = rsi.iloc[idx]
            vol_curr = df['volume'].iloc[idx]
            vol_avg = vol_sma.iloc[idx]

            # Проверка на валидность данных
            if pd.isna([close, ema9_curr, ema21_curr, bb_lower, rsi_curr, vol_avg]).any():
                return "No signal"

            # Фильтр общего тренда (упрощенный - только H1)
            trend_up = df_1h['close'].iloc[-1] > ema50_1h.iloc[-1]

            # ============ ПАТТЕРН 1: EMA Crossover + Volume ============
            ema_cross_up = (ema9_prev <= ema21_prev) and (ema9_curr > ema21_curr)
            ema_uptrend = ema9_curr > ema21_curr and ema21_curr > ema21.iloc[idx - 5]
            volume_spike = vol_curr > vol_avg * 1.2
            price_above_ema21 = close > ema21_curr

            pattern1 = (
                    trend_up and
                    ema_cross_up and
                    volume_spike and
                    25 < rsi_curr < 70  # Не перекуплен
            )

            # ============ ПАТТЕРН 2: Bollinger Bounce ============
            near_lower_bb = close <= bb_lower * 1.01  # Касание или чуть выше нижней полосы
            price_rising = close > close_prev
            rsi_oversold = 25 < rsi_curr < 45  # Перепродан, но не экстремально

            pattern2 = (
                    trend_up and
                    near_lower_bb and
                    price_rising and
                    rsi_oversold and
                    vol_curr > vol_avg * 1.1
            )

            # ============ ПАТТЕРН 3: Momentum Scalp ============
            # Быстрое движение в сторону тренда
            price_momentum = (close - df['close'].iloc[idx - 3]) / df['close'].iloc[
                idx - 3] > 0.003  # Рост >0.3% за 3 свечи
            ema_alignment = ema9_curr > ema21_curr  # EMAs выровнены
            rsi_moderate = 40 < rsi_curr < 65
            volume_ok = vol_curr > vol_avg * 1.15

            pattern3 = (
                    trend_up and
                    price_momentum and
                    ema_alignment and
                    rsi_moderate and
                    volume_ok and
                    close > bb_middle  # Выше середины BB
            )

            # ============ Debug Info ============
            if debug:
                print(f"\n=== {self.pair} Debug ===")
                print(f"Trend H1: {trend_up}")
                print(f"Close: {close:.6f}, EMA9: {ema9_curr:.6f}, EMA21: {ema21_curr:.6f}")
                print(f"BB Lower: {bb_lower:.6f}, Middle: {bb_middle:.6f}, Upper: {bb_upper:.6f}")
                print(f"RSI: {rsi_curr:.2f}")
                print(f"Volume: {vol_curr:.2f}, Avg: {vol_avg:.2f}, Ratio: {vol_curr / vol_avg:.2f}")
                print(f"Pattern 1 (EMA Cross): {pattern1}")
                print(f"Pattern 2 (BB Bounce): {pattern2}")
                print(f"Pattern 3 (Momentum): {pattern3}")

            # Возвращаем сигнал, если сработал хотя бы один паттерн
            if pattern1 or pattern2 or pattern3:
                signal_type = []
                if pattern1: signal_type.append("EMA_CROSS")
                if pattern2: signal_type.append("BB_BOUNCE")
                if pattern3: signal_type.append("MOMENTUM")
                print(f"\n=== {self.pair} Debug ===")
                print(f"Trend H1: {trend_up}")
                print(f"Close: {close:.6f}, EMA9: {ema9_curr:.6f}, EMA21: {ema21_curr:.6f}")
                print(f"BB Lower: {bb_lower:.6f}, Middle: {bb_middle:.6f}, Upper: {bb_upper:.6f}")
                print(f"RSI: {rsi_curr:.2f}")
                print(f"Volume: {vol_curr:.2f}, Avg: {vol_avg:.2f}, Ratio: {vol_curr / vol_avg:.2f}")
                print(f"Pattern 1 (EMA Cross): {pattern1}")
                print(f"Pattern 2 (BB Bounce): {pattern2}")
                print(f"Pattern 3 (Momentum): {pattern3}")
                return f"Buy ({', '.join(signal_type)})"

            return "No signal"

        except Exception as e:
            print(f"Error {self.pair}: {e}")
            import traceback
            traceback.print_exc()
            return "No signal"


# ============ Пример использования ============
# if __name__ == "__main__":
#     # Тестируем на популярных парах
#     pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT']
#
#     for pair in pairs:
#         analyzer = AnalysisCoin(pair)
#         signal = analyzer.analyze_coin(debug=True)
#         print(f"\n{pair}: {signal}")
#         print("-" * 50)