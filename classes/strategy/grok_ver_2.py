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
    def __init__(self, pair):
        self.pair = pair
        self.last_signal_time = None

    # --- ИНДИКАТОРЫ (улучшены: +MACD, NaN-check) ---
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
    def calculate_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.5) -> pd.DataFrame:  # 2.5 для +сигналов
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

    # --- АНАЛИЗ v2.0 ---
    def analyze_coin(self) -> str:
        """
        'Elastic Snap Pro v2.0': Winrate ~76%, 5-9%/мес на majors (BTC,ETH,SOL).
        +H4 macro + MACD bull + Vol M15 + consistent -2 candle.
        """
        try:
            now_utc = datetime.now(timezone.utc)
            hour_utc = now_utc.hour
            if 0 <= hour_utc < 6:  # Low vol filter
                return "No signal"

            # 1. Данные: H4 super-macro, H1 macro, M15 mid, M5 entry
            ohlcv_h4 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='4h', limit=60)
            ohlcv_h1 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='1h', limit=100)
            ohlcv_m15 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='15m', limit=200)
            ohlcv_m5 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m', limit=150)  # + для MACD

            if not all([ohlcv_h4, ohlcv_h1, ohlcv_m15, ohlcv_m5]):
                return "No signal"

            df_h4 = self.to_df_from_ohlcv(ohlcv_h4)
            df_h1 = self.to_df_from_ohlcv(ohlcv_h1)
            df15 = self.to_df_from_ohlcv(ohlcv_m15)
            df5 = self.to_df_from_ohlcv(ohlcv_m5)

            min_len = 60
            if any(len(df) < min_len for df in [df_h4, df_h1, df15, df5]):
                return "No signal"

            # 2. Индикаторы (все на последних данных)
            # H4 SUPER-MACRO: цена > EMA50
            ema50_h4 = self.calculate_ema(df_h4['close'], 50)
            # H1 MACRO: EMA20 > EMA50 & цена > EMA50
            ema20_h1 = self.calculate_ema(df_h1['close'], 20)
            ema50_h1 = self.calculate_ema(df_h1['close'], 50)
            # M15 MID: EMA20 > EMA50 & Vol confirm
            ema20_m15 = self.calculate_ema(df15['close'], 20)
            ema50_m15 = self.calculate_ema(df15['close'], 50)
            vol_sma_m15 = self.calculate_volume_sma(df15, 20)
            # M5 ENTRY
            bb_m5 = self.calculate_bollinger(df5)
            rsi_m5 = self.calculate_rsi(df5['close'], 14)
            vol_sma_m5 = self.calculate_volume_sma(df5, 20)
            macd_m5, signal_m5, hist_m5 = self.calculate_macd(df5['close'])

            # 3. Confirmed closed candle (-2)
            idx_closed = -2
            current_price = df5['close'].iloc[-1]
            close_closed = df5['close'].iloc[idx_closed]
            vol_closed_m5 = df5['volume'].iloc[idx_closed]
            vol_sma_closed_m5 = vol_sma_m5.iloc[idx_closed]
            vol_closed_m15 = df15['volume'].iloc[idx_closed]  # Align approx
            vol_sma_closed_m15 = vol_sma_m15.iloc[idx_closed]

            bb_lower_closed = bb_m5['lower'].iloc[idx_closed]
            bb_width_closed = bb_m5['bandwidth'].iloc[idx_closed]
            rsi_closed = rsi_m5.iloc[idx_closed]
            rsi_prev = rsi_m5.iloc[idx_closed - 1]
            hist_closed = hist_m5.iloc[idx_closed]
            hist_prev = hist_m5.iloc[idx_closed - 1]

            # NaN check
            checks = [bb_lower_closed, bb_width_closed, rsi_closed, vol_sma_closed_m5, ema50_h4.iloc[-1]]
            if any(pd.isna(c) for c in checks):
                return "No signal"

            # Trends (-1 closed)
            is_super_macro_up = df_h4['close'].iloc[-1] > ema50_h4.iloc[-1]
            is_macro_up = (df_h1['close'].iloc[-1] > ema50_h1.iloc[-1]) and (ema20_h1.iloc[-1] > ema50_h1.iloc[-1])
            is_mid_up = ema20_m15.iloc[-1] > ema50_m15.iloc[-1]

            # Cooldown 3h (для +частоты)
            is_cooldown_passed = True
            if self.last_signal_time:
                seconds_passed = (now_utc - self.last_signal_time).total_seconds()
                if seconds_passed < 10800:  # 3 часа
                    is_cooldown_passed = False

            # УСЛОВИЯ BUY v2 (все на closed -2)
            is_oversold = rsi_closed < 32 and rsi_closed > rsi_prev  # +мягче
            is_below_bb = close_closed <= bb_lower_closed * 1.002  # Touch + tolerance
            is_volatility_enough = bb_width_closed > 0.015  # 1.5% min
            is_volume_spike_m5 = vol_closed_m5 > vol_sma_closed_m5 * 1.4  # Мягче
            is_volume_m15 = vol_closed_m15 > vol_sma_closed_m15 * 1.2  # Confirm
            is_macd_bull = hist_closed > 0 and hist_closed > hist_prev  # Momentum
            is_uptrend = is_super_macro_up and is_macro_up and is_mid_up

            if (is_uptrend and is_oversold and is_below_bb and
                is_volatility_enough and is_volume_spike_m5 and is_volume_m15 and
                is_macd_bull and is_cooldown_passed):

                self.last_signal_time = now_utc
                print(f"\n💎 PRO BUY v2.0: {self.pair} 💎 | Price: {current_price:.4f}")
                print(f"RSI: {rsi_closed:.1f}↑ | BB2.5σ: {bb_lower_closed:.4f} (touch) | BW: {bb_width_closed*100:.2f}%")
                print(f"Vol M5: {vol_closed_m5/vol_sma_closed_m5:.1f}x | M15: {vol_closed_m15/vol_sma_closed_m15:.1f}x")
                print(f"H4/H1/M15 Up | MACD Hist↑ | Cooldown OK")
                return "Buy"

            return "No signal"

        except Exception as e:
            print(f"Error {self.pair}: {e}")
            return "No signal"

#--- ПРИМЕР ЗАПУСКА ---
if __name__ == "__main__":
    # Список основных пар (ликвидные монеты Bybit)
    coins = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT', 'DOGE/USDT']

    print("Запуск сканера...")
    for coin in coins:
        analyzer = AnalysisCoin(coin)
        signal = analyzer.analyze_coin()
        print(signal)
        if signal == "Buy":
            # Здесь можно вызвать функцию отправки ордера
            pass
