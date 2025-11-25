import ccxt
import pandas as pd
import numpy as np
from datetime import datetime

EXCHANGE = ccxt.bybit()

class AnalysisCoin:
    last_signal_time = {}  # Для хранения времени последнего сигнала

    def __init__(self, pair):
        self.pair = pair

    # --- вспомогательные индикаторы (локальные реализации) ---
    @staticmethod
    def add_bop(df: pd.DataFrame, smooth: int = 1) -> pd.Series:
        # BOP = (close - open) / (high - low)
        s = (df['close'] - df['open']) / (df['high'] - df['low']).replace(0, np.nan)
        if smooth > 1:
            s = s.rolling(smooth).mean()
        return s

    @staticmethod
    def add_mean_reversion(df: pd.DataFrame, period: int = 20, mult: float = 2.0) -> pd.DataFrame:
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = sma + mult * std
        lower = sma - mult * std
        mr = pd.DataFrame({'sma': sma, 'upper': upper, 'lower': lower})
        return mr

    @staticmethod
    def add_donchian(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        dh = df['high'].rolling(period).max()
        dl = df['low'].rolling(period).min()
        return pd.DataFrame({'donchian_high': dh, 'donchian_low': dl})

    @staticmethod
    def to_df_from_ohlcv(ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open','high','low','close','volume']:
            df[col] = df[col].astype(float)
        df = df.drop_duplicates('timestamp').sort_values('timestamp').reset_index(drop=True)
        return df

    # --- основная функция: только BUY сигнал ---
    def analyze_coin(self, tol: float = 0.01) -> str:
        """
        Возвращает "Buy" или "No signal".
        Параметры:
          tol - толерантность при сравнении с границами mean reversion (например 0.01 == 1%)
        Логика (по вашему описанию Bomberman, buy-only):
          - BOP (M30) > 0
          - Цена на M15 <= lower_MR * (1 + tol)
          - Цена на M5 > предыдущий donchian_high (пробой вверх на M5)
        Все сравнения делаются на последних ЗАКРЫТЫХ барах (чтобы не смотреть в будущее).
        """
        try:
            # --- fetch OHLCV для трёх таймфреймов ---
            # Берём достаточный запас баров чтобы рассчитать индикаторы (periodы ~20)
            ohlcv_m30 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='30m', limit=400)
            ohlcv_m15 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='15m', limit=400)
            ohlcv_m5  = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m',  limit=800)

            df30 = self.to_df_from_ohlcv(ohlcv_m30)
            df15 = self.to_df_from_ohlcv(ohlcv_m15)
            df5  = self.to_df_from_ohlcv(ohlcv_m5)

            # минимальные проверки длины
            if len(df30) < 30 or len(df15) < 30 or len(df5) < 60:
                return "No signal"

            # --- рассчитываем индикаторы (rolling, только исторические данные) ---
            # Используем последние закрытые бары: last_closed index = -2
            # (последний элемент df.iloc[-1] может быть формирующейся свечой)
            bop_series = self.add_bop(df30, smooth=3)          # сглажим BOP чуть-чуть
            mr15 = self.add_mean_reversion(df15, period=20, mult=2.0)
            don5 = self.add_donchian(df5, period=20)

            # индекс закрытой свечи (последняя полностью закрытая)
            idx30 = -2
            idx15 = -2
            idx5  = -2

            # извлекаем значения индикаторов на последних закрытых барах
            bop_now = bop_series.iloc[idx30]
            # mean reversion lower на M15
            lower_m15 = mr15['lower'].iloc[idx15]
            sma_m15   = mr15['sma'].iloc[idx15]
            # donchian предыдущий high на M5 (для пробоя берем именно пред. уровень)
            don_prev_high = don5['donchian_high'].iloc[idx5 - 1] if len(don5) >= 3 else don5['donchian_high'].iloc[idx5]
            # цена - используем закрытую цену M5 (последняя закрытая на коротком ТФ)
            price_m5 = df5['close'].iloc[idx5]

            # базовые проверки на NaN
            if any(pd.isna(x) for x in [bop_now, lower_m15, don_prev_high, price_m5]):
                return "No signal"

            # --- логика входа (BUY) ---
            # 1) Фильтр тренда/сил: BOP > 0 на M30
            if not (bop_now > 0):
                return "No signal"

            # 2) Перепроданность на M15: цена <= lower * (1 + tol)
            #    (используем значение lower для последней закрытой M15 свечи)
            if not (price_m5 <= lower_m15 * (1.0 + tol)):
                return "No signal"

            # 3) Пробой на M5: закрытие > предыдущий donchian_high
            if not (price_m5 > don_prev_high):
                return "No signal"

            # Дополнительные простые фильтры (рекомендуемые, необязательные):
            # - объём на M5 должен быть не слишком маленьким (относительно среднего)
            vol_m5 = df5['volume'].iloc[idx5]
            avg_vol_m5 = df5['volume'].rolling(window=20).mean().iloc[idx5]
            if pd.notna(avg_vol_m5) and vol_m5 < avg_vol_m5 * 0.5:
                # слишком маленький объём — сигнал слабый
                return "No signal"

            # - небольшой sanity-check по волатильности: ATR на M15 > медленный порог (зависит от цены)
            # вычислим ATR простым способом на M15
            tr15 = pd.concat([
                df15['high'] - df15['low'],
                (df15['high'] - df15['close'].shift()).abs(),
                (df15['low'] - df15['close'].shift()).abs()
            ], axis=1).max(axis=1)
            atr15 = tr15.rolling(14).mean().iloc[idx15]
            if pd.notna(atr15) and atr15 < 0.002 * price_m5:  # например минимальная волатильность 0.2% от цены
                return "No signal"

            # Все условия пройдены -> Buy
            # Защита повторных сигналов: не даём сигналы чаще, чем один на X минут (опционально)
            now = datetime.utcnow()
            last_ts = AnalysisCoin.last_signal_time.get(self.pair)
            cooldown_minutes = 30
            if last_ts is not None:
                delta = (now - last_ts).total_seconds() / 60.0
                if delta < cooldown_minutes:
                    return "No signal"
            # записываем время сигнала
            AnalysisCoin.last_signal_time[self.pair] = now

            print(f"[{now.isoformat()}] Buy signal for {self.pair}: price={price_m5:.4f}, bop={bop_now:.4f}, lower_M15={lower_m15:.4f}, don_prev_high={don_prev_high:.4f}")
            print(f"📣📣📣 Найден сигнал на для {self.pair}! 📣📣📣")
            return "Buy"

        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair}: {e}")
            return "No signal"


# COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

# COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LTCUSDT", "ATOMUSDT",
# "APEUSDT", "LINKUSDT", "NEARUSDT", "PEPEUSDT", "SHIBUSDT", "IMXUSDT", "TONUSDT", "SANDUSDT", "XLMUSDT",
# "ONDOUSDT", "MNTUSDT", "SWEATUSDT", "TRXUSDT", "DOGSUSDT"]
# for coin in COINS:
#     spot = AnalysisCoin(coin)
#     result = spot.analyze_coin() #timeframe="5m"
#     print(result)