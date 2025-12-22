import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timezone

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
    def calculate_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.5) -> pd.DataFrame:
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
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

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

    def analyze_coin(self) -> str:
        """
        Анализ на покупку на заданном timeframe (например, '5m').
        Стратегия: multi-TF с H4/H1/M15/M5, сигнал на -2 свече.
        Возвращает "Buy" если условия выполнены, иначе "No signal".
        """
        try:
            # Фильтр низкой волатильности
            now_utc = datetime.now(timezone.utc)
            if 0 <= now_utc.hour < 6:
                return "No signal"

            # Данные: всегда multi-TF (H4 гибкий, но игнорировать для простоты)
            ohlcv_h4 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='4h', limit=60)
            ohlcv_h1 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='1h', limit=100)
            ohlcv_m15 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='15m', limit=200)
            ohlcv_tf = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m', limit=150)  # Используемый timeframe для entry (вместо M5)

            if not all([ohlcv_h4, ohlcv_h1, ohlcv_m15, ohlcv_tf]):
                return "No signal"

            df_h4 = self.to_df_from_ohlcv(ohlcv_h4)
            df_h1 = self.to_df_from_ohlcv(ohlcv_h1)
            df15 = self.to_df_from_ohlcv(ohlcv_m15)
            df_tf = self.to_df_from_ohlcv(ohlcv_tf)

            if any(len(df) < 60 for df in [df_h4, df_h1, df15, df_tf]):
                return "No signal"

            # Индикаторы
            ema50_h4 = self.calculate_ema(df_h4['close'], 50)
            ema20_h1 = self.calculate_ema(df_h1['close'], 20)
            ema50_h1 = self.calculate_ema(df_h1['close'], 50)
            ema20_m15 = self.calculate_ema(df15['close'], 20)
            ema50_m15 = self.calculate_ema(df15['close'], 50)
            vol_sma_m15 = self.calculate_volume_sma(df15, 20)
            bb_tf = self.calculate_bollinger(df_tf)
            rsi_tf = self.calculate_rsi(df_tf['close'], 14)
            vol_sma_tf = self.calculate_volume_sma(df_tf, 20)
            macd_tf, signal_tf, hist_tf = self.calculate_macd(df_tf['close'])

            # Данные на закрытой -2 свече
            idx_closed = -2
            close_closed = df_tf['close'].iloc[idx_closed]
            vol_closed_tf = df_tf['volume'].iloc[idx_closed]
            vol_sma_closed_tf = vol_sma_tf.iloc[idx_closed]
            vol_closed_m15 = df15['volume'].iloc[idx_closed]
            vol_sma_closed_m15 = vol_sma_m15.iloc[idx_closed]
            bb_lower_closed = bb_tf['lower'].iloc[idx_closed]
            bb_width_closed = bb_tf['bandwidth'].iloc[idx_closed]
            rsi_closed = rsi_tf.iloc[idx_closed]
            rsi_prev = rsi_tf.iloc[idx_closed - 1]
            hist_closed = hist_tf.iloc[idx_closed]
            hist_prev = hist_tf.iloc[idx_closed - 1]

            # Проверки на неопределенность
            checks = [bb_lower_closed, bb_width_closed, rsi_closed, vol_sma_closed_tf, ema50_h4.iloc[-1]]
            if any(pd.isna(c) for c in checks):
                return "No signal"

            # Тренды
            is_super_macro_up = df_h4['close'].iloc[-1] > ema50_h4.iloc[-1]
            is_macro_up = df_h1['close'].iloc[-1] > ema50_h1.iloc[-1] and ema20_h1.iloc[-1] > ema50_h1.iloc[-1]
            is_mid_up = ema20_m15.iloc[-1] > ema50_m15.iloc[-1]

            # Условия Buy
            is_oversold = rsi_closed < 32 and rsi_closed > rsi_prev
            is_below_bb = close_closed <= bb_lower_closed * 1.002
            is_volatility_enough = bb_width_closed > 0.015
            is_volume_spike_tf = vol_closed_tf > vol_sma_closed_tf * 1.4
            is_volume_m15 = vol_closed_m15 > vol_sma_closed_m15 * 1.2
            is_macd_bull = hist_closed > 0 and hist_closed > hist_prev
            is_uptrend = is_super_macro_up and is_macro_up and is_mid_up

            if is_uptrend and is_oversold and is_below_bb and is_volatility_enough and is_volume_spike_tf and is_volume_m15 and is_macd_bull:
                return "Buy"

            return "No signal"

        except Exception as e:
            print(f"Error {self.pair}: {e}")
            return "No signal"

# Пример запуска с ордером
# Пример использования
# if __name__ == "__main__":
#     # Список пар
#     coins = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT', 'DOGE/USDT',
#              'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LTC/USDT', 'ATOM/USDT', 'APE/USDT',
#              'LINK/USDT', 'NEAR/USDT', 'PEPE/USDT', 'SHIB/USDT', 'IMX/USDT', 'TON/USDT',
#              'SAND/USDT', 'XLM/USDT', 'ONDO/USDT', 'MNT/USDT', 'TRX/USDT', 'DOGS/USDT',
#              'TWT/USDT', 'AST/USDT']
#
#     # Заданный timeframe (например, '5m' для скальпинга)
#     timeframe = '5m'
#
#     print("Запуск сканера...")
#     for coin in coins:
#         analyzer = AnalysisCoin(coin)
#         signal = analyzer.analyze_coin(timeframe)
#         print(f"{coin}: {signal}")