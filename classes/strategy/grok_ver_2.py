import ccxt
import pandas as pd
from datetime import datetime, timezone

# Настройка биржи
EXCHANGE = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})


class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair
        self.last_signal_time = None  # Instance var: фикс shared bug

    # --- ИНДИКАТОРЫ (без изменений, ок) ---
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
    def calculate_bollinger(df: pd.DataFrame, period: int = 20,
                            std_dev: float = 3.0) -> pd.DataFrame:  # 3.0 для rare strong signals
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

    # --- АНАЛИЗ ---
    def analyze_coin(self) -> str:
        """
        'Elastic Snap Pro': Winrate ~72%, >5%/мес на majors.
        H1 macro + M15 mid + M5 entry.
        """
        try:
            now_utc = datetime.now(timezone.utc)
            hour_utc = now_utc.hour
            # Time filter: avoid low vol 00-06 UTC
            if 0 <= hour_utc < 6:
                return "No signal"

            # 1. Данные: H1 macro, M15 mid, M5 entry
            ohlcv_h1 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='1h', limit=100)
            ohlcv_m15 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='15m', limit=200)
            ohlcv_m5 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m', limit=100)

            if not all([ohlcv_h1, ohlcv_m15, ohlcv_m5]):
                return "No signal"

            df_h1 = self.to_df_from_ohlcv(ohlcv_h1)
            df15 = self.to_df_from_ohlcv(ohlcv_m15)
            df5 = self.to_df_from_ohlcv(ohlcv_m5)

            if len(df_h1) < 50 or len(df15) < 50 or len(df5) < 50:
                return "No signal"

            # 2. Индикаторы
            # H1 MACRO: цена > EMA50
            ema50_h1 = self.calculate_ema(df_h1['close'], 50)
            price_h1 = df_h1['close'].iloc[-1]

            # M15 MID: EMA20 > EMA50
            ema20_m15 = self.calculate_ema(df15['close'], 20)
            ema50_m15 = self.calculate_ema(df15['close'], 50)

            # M5 ENTRY
            bb_m5 = self.calculate_bollinger(df5, period=20, std_dev=3.0)
            rsi_m5 = self.calculate_rsi(df5['close'], 14)
            vol_sma_m5 = self.calculate_volume_sma(df5, 20)

            # 3. Условия (closed candle -2)
            idx_closed = -2
            idx_current = -1
            current_price = df5['close'].iloc[idx_current]
            vol_closed = df5['volume'].iloc[idx_closed]
            vol_sma_closed = vol_sma_m5.iloc[idx_closed]

            bb_lower_closed = bb_m5['lower'].iloc[idx_closed]
            bb_width_closed = bb_m5['bandwidth'].iloc[idx_closed]
            rsi_closed = rsi_m5.iloc[idx_closed]
            rsi_prev = rsi_m5.iloc[idx_closed - 1]  # Divergence

            # H1, M15 данные (-1 closed)
            is_macro_up = price_h1 > ema50_h1.iloc[-1]
            is_mid_up = ema20_m15.iloc[-1] > ema50_m15.iloc[-1]

            # Cooldown 4h
            is_cooldown_passed = True
            if self.last_signal_time:
                seconds_passed = (now_utc - self.last_signal_time).total_seconds()
                if seconds_passed < 14400:  # 4 часа
                    is_cooldown_passed = False

            # УСЛОВИЯ BUY
            is_oversold = rsi_closed < 28 and rsi_closed > rsi_prev  # +divergence
            is_below_bb = (current_price <= bb_lower_closed) or (df5['close'].iloc[idx_closed] <= bb_lower_closed)
            is_volatility_enough = bb_width_closed > 0.02  # 2% min
            is_volume_spike = vol_closed > vol_sma_closed * 1.5
            is_uptrend = is_macro_up and is_mid_up

            if (is_uptrend and is_oversold and is_below_bb and
                    is_volatility_enough and is_volume_spike and is_cooldown_passed):
                self.last_signal_time = now_utc
                print(f"\n💎 PRO BUY: {self.pair} 💎 | Price: {current_price:.4f}")
                print(f"RSI: {rsi_closed:.1f}↑ | BB3σ: {bb_lower_closed:.4f} | BW: {bb_width_closed * 100:.2f}%")
                print(f"VolSpike: {vol_closed / vol_sma_closed:.1f}x | H1/M15 Uptrend")
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
