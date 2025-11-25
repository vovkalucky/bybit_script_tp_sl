import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, UTC
from config import get_config
config = get_config()
# Настрой Bybit API
# EXCHANGE = ccxt.bybit({
#     'apiKey': config['api_key'],
#     'secret': config['api_secret']
# })
EXCHANGE = ccxt.bybit()

class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair
        self.entry_price = None  # Для треккинга входа

    # --- Вспомогательные индикаторы ---
    @staticmethod
    def add_bop(df: pd.DataFrame, smooth: int = 3) -> pd.Series:
        s = (df['close'] - df['open']) / (df['high'] - df['low']).replace(0, np.nan)
        return s.rolling(smooth).mean() if smooth > 1 else s

    @staticmethod
    def add_mean_reversion(df: pd.DataFrame, period: int = 20, mult: float = 2.0) -> pd.DataFrame:
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = sma + mult * std
        lower = sma - mult * std
        return pd.DataFrame({'sma': sma, 'upper': upper, 'lower': lower})

    @staticmethod
    def add_donchian(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        # Donchian: max/min за period предыдущих баров
        dh = df['high'][:-1].rolling(period).max()  # Без включения текущей свечи для пробоя
        dl = df['low'][:-1].rolling(period).max()   # Аналогично
        return pd.DataFrame({'donchian_high': dh, 'donchian_low': dl})

    @staticmethod
    def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def to_df_from_ohlcv(ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        df = df.drop_duplicates('timestamp').sort_values('timestamp').reset_index(drop=True)
        return df

    def analyze_coin(self, tol: float = 0.01) -> str:
        """
        Выдает "Buy" или "No signal" на основе перепроданного пробоя.
        Доработки: Улучшенный Donchian (сравнение с предыдущим уровнем), добавлен RSI < 30.
        """
        try:
            ohlcv_m30 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='30m', limit=400)
            ohlcv_m15 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='15m', limit=400)
            ohlcv_m5 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m', limit=800)

            df30 = self.to_df_from_ohlcv(ohlcv_m30)
            df15 = self.to_df_from_ohlcv(ohlcv_m15)
            df5 = self.to_df_from_ohlcv(ohlcv_m5)

            if len(df30) < 30 or len(df15) < 30 or len(df5) < 60:
                return "No signal"

            # Индикаторы
            bop_series = self.add_bop(df30, smooth=3)
            mr15 = self.add_mean_reversion(df15, period=20, mult=2.0)
            don5 = self.add_donchian(df5, period=20)
            rsi15 = self.add_rsi(df15, period=14)

            idx30 = -2
            idx15 = -2
            idx5 = -2

            bop_now = bop_series.iloc[idx30]
            lower_m15 = mr15['lower'].iloc[idx15]
            rsi_now = rsi15.iloc[idx15]
            don_prev_high = don5['donchian_high'].iloc[idx5]  # Предыдущий уровень (уже рассчитан без текущей свечи)
            price_m5 = df5['close'].iloc[idx5]

            if any(pd.isna(x) for x in [bop_now, lower_m15, rsi_now, don_prev_high, price_m5]):
                return "No signal"

            # Логика BUY
            if not (bop_now > 0 and price_m5 <= lower_m15 * (1.0 + tol) and price_m5 > don_prev_high and rsi_now < 30):
                return "No signal"

            # Фильтры
            vol_m5 = df5['volume'].iloc[idx5]
            avg_vol = df5['volume'].rolling(20).mean().iloc[idx5]
            if pd.notna(avg_vol) and vol_m5 < avg_vol * 0.7:
                return "No signal"

            tr15 = pd.concat([
                df15['high'] - df15['low'],
                (df15['high'] - df15['close'].shift()).abs(),
                (df15['low'] - df15['close'].shift()).abs()
            ], axis=1).max(axis=1)
            atr15 = tr15.rolling(14).mean().iloc[idx15]
            if pd.notna(atr15) and atr15 < 0.005 * price_m5:
                return "No signal"

            # Сигнал
            now = datetime.now(UTC)
            print(f"[{now}] Buy {self.pair}: price={price_m5:.4f}, BOP={bop_now:.4f}, lower={lower_m15:.4f}, don_prev={don_prev_high:.4f}, RSI={rsi_now:.2f}")
            self.entry_price = price_m5
            return "Buy"

        except Exception as e:
            print(f"Error {self.pair}: {e}")
            return "No signal"

    def check_sell(self, entry_price: float, target: float = 0.01) -> str:
        """
        Проверяет рост на 1% для SELL. Вызывай после BUY.
        """
        try:
            ohlcv_1m = EXCHANGE.fetch_ohlcv(self.pair, timeframe='1m', limit=10)
            df1m = self.to_df_from_ohlcv(ohlcv_1m)
            current_price = df1m['close'].iloc[-1]
            if current_price >= entry_price * (1 + target):
                return "Sell"
        except Exception as e:
            print(f"Sell check error {self.pair}: {e}")
        return "Hold"

# Инициализация
pairs = ['BTC/USDT', 'ETH/USDT']
analyzers = {pair: AnalysisCoin(pair) for pair in pairs}

for pair in pairs:
    buy_signal = analyzers[pair].analyze_coin(tol=0.01)
    if buy_signal == "Buy":
        print(buy_signal,  pair)

