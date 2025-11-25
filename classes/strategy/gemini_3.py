import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, UTC

# Настройка биржи (включаем RateLimit для стабильности)
EXCHANGE = ccxt.bybit({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}  # Используем фьючерсы (swap) или 'spot'
})


class AnalysisCoin:
    last_signal_time = {}  # Храним время последнего сигнала

    def __init__(self, pair):
        self.pair = pair

    # --- ИНДИКАТОРЫ ---

    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        # Более точный расчет (Smoothed Moving Average как в TradingView)
        # Но для простоты используем rolling mean или ewm (exponential weighted)
        # Используем Wilder's smoothing для точности с TradingView
        delta = series.diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0

        # EMA с alpha=1/14 дает результат близкий к RSI Wilder
        roll_up1 = up.ewm(span=period, adjust=False).mean()
        roll_down1 = down.abs().ewm(span=period, adjust=False).mean()

        rs = roll_up1 / roll_down1
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def calculate_bollinger(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return pd.DataFrame({'sma': sma, 'upper': upper, 'lower': lower})

    @staticmethod
    def calculate_ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def to_df_from_ohlcv(ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        # Сортировка и удаление дублей
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df

    # --- ОСНОВНАЯ ФУНКЦИЯ ---
    def analyze_coin(self) -> str:
        """
        Стратегия: RSI + Bollinger Dip на восходящем тренде.
        Цель: Поймать откат для заработка 1%.
        """
        try:
            # 1. Загрузка данных (M15 для тренда, M5 для входа)
            ohlcv_m15 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='15m', limit=200)
            ohlcv_m5 = EXCHANGE.fetch_ohlcv(self.pair, timeframe='5m', limit=200)

            df15 = self.to_df_from_ohlcv(ohlcv_m15)
            df5 = self.to_df_from_ohlcv(ohlcv_m5)

            if len(df15) < 100 or len(df5) < 100:
                return "No signal"

            # 2. Расчет индикаторов

            # --- M15 (Тренд) ---
            # EMA 200 определяет долгосрочный тренд на этом таймфрейме
            ema200_m15 = self.calculate_ema(df15['close'], 200)

            # --- M5 (Точка входа) ---
            bb_m5 = self.calculate_bollinger(df5, period=20, std_dev=2.0)
            rsi_m5 = self.calculate_rsi(df5['close'], period=14)

            # 3. Анализ (берем предпоследнюю свечу/закрытую, индекс -2)
            # Индекс -1 — это текущая (незакрытая) свеча. Для тестов и надежности берем -2.
            idx = -2

            close_current_m5 = df5['close'].iloc[idx]
            close_current_m15 = df15['close'].iloc[idx]  # ВНИМАНИЕ: упрощение, по-хорошему надо матчить по времени

            ema_trend_val = ema200_m15.iloc[idx]

            bb_lower = bb_m5['lower'].iloc[idx]
            rsi_val = rsi_m5.iloc[idx]

            # Проверка на валидность данных
            if pd.isna(ema_trend_val) or pd.isna(bb_lower) or pd.isna(rsi_val):
                return "No signal"

            # ================= УСЛОВИЯ СТРАТЕГИИ =================

            # A. Фильтр тренда: Цена на M15 выше EMA 200.
            # Мы не хотим покупать дно на медвежьем рынке, мы хотим покупать откаты на бычьем.
            is_uptrend = close_current_m15 > ema_trend_val

            # B. Перепроданность: RSI < 30 (или 32 для более частых входов)
            is_oversold_rsi = rsi_val < 32

            # C. Цена у нижней границы канала: Цена <= Lower Band * 1.002 (даем маленький допуск 0.2%)
            is_at_lower_band = close_current_m5 <= (bb_lower * 1.003)

            # D. Объем (опционально): Объем выше среднего (подтверждение активности)
            vol_mean = df5['volume'].rolling(20).mean().iloc[idx]
            is_volume_ok = df5['volume'].iloc[idx] > vol_mean * 0.8

            # --- ЛОГИКА ВХОДА ---

            if is_uptrend and is_oversold_rsi and is_at_lower_band and is_volume_ok:

                # Защита от спама сигналами (кулдаун 60 минут на пару)
                now = datetime.now(UTC)
                last_ts = AnalysisCoin.last_signal_time.get(self.pair)
                if last_ts:
                    delta_min = (now - last_ts).total_seconds() / 60.0
                    if delta_min < 60:
                        return "No signal"

                # Формируем сигнал
                AnalysisCoin.last_signal_time[self.pair] = now

                print(f"\n🚀 BUY SIGNAL: {self.pair} 🚀")
                print(f"Checking Time: {now.strftime('%H:%M:%S')}")
                print(f"Price: {close_current_m5} | Trend EMA200: {ema_trend_val:.4f}")
                print(f"RSI (M5): {rsi_val:.2f} | BB Lower: {bb_lower:.4f}")
                print("--------------------------------------------------")

                return "Buy"

            return "No signal"

        except Exception as e:
            print(f"Error analysing {self.pair}: {e}")
            return "No signal"


# --- ПРИМЕР ЗАПУСКА ---
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