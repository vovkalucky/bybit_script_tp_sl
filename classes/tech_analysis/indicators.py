import pandas as pd
import numpy as np

class Indicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if not all(col in df.columns for col in ['high', 'low', 'close']):
            raise ValueError("DataFrame must contain 'high', 'low', 'close' columns.")

    def ema(self, column: str, period: int) -> pd.Series:
        return self.df[column].ewm(span=period, adjust=False).mean()

    def rsi(self, column: str = 'close', period: int = 14) -> pd.Series:
        delta = self.df[column].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(0)

    def macd(self, column: str = 'close', fast=12, slow=26, signal=9):
        ema_fast = self.ema(column, fast)
        ema_slow = self.ema(column, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        hist = macd_line - signal_line
        return macd_line, signal_line, hist

    def bollinger_bands(self, column: str = 'close', period: int = 20, dev: float = 2.0):
        sma = self.df[column].rolling(window=period).mean()
        std = self.df[column].rolling(window=period).std()
        upper = sma + dev * std
        lower = sma - dev * std
        return upper, sma, lower

    def true_range(self) -> pd.Series:
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    def atr(self, period: int = 14) -> pd.Series:
        tr = self.true_range()
        return tr.rolling(window=period).mean()

    def adx(self, period: int = 14) -> pd.Series:
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']

        plus_dm = high.diff()
        minus_dm = low.diff()

        plus_dm = np.where(
            (plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0
        )
        minus_dm = np.where(
            (minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0
        )

        tr = self.true_range()
        atr_val = tr.rolling(window=period).mean()

        plus_di = 100 * (pd.Series(plus_dm).rolling(window=period).mean() / atr_val)
        minus_di = 100 * (pd.Series(minus_dm).rolling(window=period).mean() / atr_val)

        dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)) * 100
        return dx.rolling(window=period).mean()