from typing import List
from pybit.unified_trading import HTTP
from tradingview_ta import TA_Handler
from config import get_config
import ccxt
import pandas as pd
import pandas_ta as ta


config = get_config()

class TechAnalysis:
    session = HTTP(api_key=config['api_key'],
                   api_secret=config['api_secret'],
                   demo=config['demo'],
                   max_retries=10,
                   retry_delay=10)

    @classmethod
    def get_volume_from_klines(cls, symbol: str, interval: str, count: int) -> List[float]:
        klines = cls.session.get_kline(category="spot", symbol=symbol, interval=interval)
        volumes = klines['result']['list']
        volumes_list = []
        for volume in volumes[0:count]:
            volumes_list.append(float(volume[5]))
        volumes_list = volumes_list[::-1]
        return volumes_list

    @staticmethod
    def avg_volume(volumes_list: List[float]) -> float:
        return round(sum(volumes_list) / len(volumes_list), 3) if volumes_list else 0

    @staticmethod
    def check_volumes(coin: str, interval: str, count: int, threshold: float = 1.2) -> bool:
        try:
            volumes_list = TechAnalysis.get_volume_from_klines(coin, interval, count)
            if not volumes_list:
                print(f"[check_volumes] Ошибка: пустой список объемов для {coin}")
                return False
            current_volume = float(volumes_list[-1])
            avg_volume = TechAnalysis.avg_volume(volumes_list)
            #threshold = 1.2  # Допустим, сигнал дается при превышении на 20%
            print(f"(current_volume) {current_volume} (avg_volume) {avg_volume}")
            return current_volume > avg_volume * threshold
        except Exception as e:
            print(f"[check_volumes]: {e}")
            return False

    @classmethod
    def get_klines(cls, symbol: str, interval: str, limit: int = 14):
        """Функция для получения свечей
        :param symbol BTCUSDT,
        :param interval 1,3,5,15,30,60,120,240,360,720,D,W,M
        :param limit количество возвращаемых свечей
        :return reverse_klines массив свечей в формате [tohlcv] в хронологическом порядке:
        0 свеча - самая старая, последняя - текущая. Пример: ['1742501700000', '1971.43', '1978.18', '1971.43', '1977.37', '218.87295', '432217.0390999']"""
        klines = cls.session.get_kline(category="spot", symbol=symbol, interval=interval, limit=limit)
        reverse_klines = klines['result']['list'][::-1]
        return reverse_klines

    @classmethod
    def calculate_atr(cls, candles, period=14) -> float:
        """
        Рассчитывает Average True Range (ATR) для данного набора свечей.

        :param candles: Список свечей в формате [timestamp, open, high, low, close, ...]
        :param period: Период для расчета ATR (по умолчанию 14)
        :return: Значение ATR, округленное до 3 знаков
        """
        if len(candles) < period:
            raise ValueError("Недостаточно данных для расчета ATR")

        tr_values = []

        for i in range(1, len(candles)):
            high = float(candles[i][2])
            low = float(candles[i][3])
            close_prev = float(candles[i - 1][4])

            tr = max(high - low, abs(high - close_prev), abs(low - close_prev))
            tr_values.append(tr)

        # Вычисляем ATR через SMA первых period значений
        atr = sum(tr_values[:period]) / period

        # Используем формулу экспоненциального сглаживания
        for i in range(period, len(tr_values)):
            atr = (atr * (period - 1) + tr_values[i]) / period

        return round(atr, 3)

    @classmethod
    def check_trend_by_atr(cls, symbol: str, interval:str, limit:int = 20) -> bool:
        klines = TechAnalysis.get_klines(symbol, interval, limit)
        atr = TechAnalysis.calculate_atr(klines)
        previous_close = float(klines[-2][4])
        close = float(klines[-1][4])
        #print(f"previous_close: {previous_close} close {close}")
        #print(f"atr {atr}")
        return close > (previous_close + atr)

    @classmethod
    def find_imbalance(
            cls,
            symbol: str,
            interval: str,
            direction: str,
            limit: int = 10,
            imbalance: float = 0.7,
    ) -> bool:

        klines = cls.get_klines(symbol, interval, limit)

        if direction != "bear":
            return False

        third_low = float(klines[-4][3])  # low свечи 1
        second_low = float(klines[-3][3])  # low свечи 2
        first_high = float(klines[-2][2])  # high свечи 3
        current = float(klines[-1][4])  # текущая цена

        # 1️⃣ Импульс вниз
        impulse = second_low < third_low

        # 2️⃣ Размер дисбаланса
        fvg_percent = (third_low - first_high) / third_low * 100
        imbalance_ok = fvg_percent >= imbalance

        # 3️⃣ Цена вернулась в зону
        in_fvg_zone = second_low <= current <= first_high

        if impulse and imbalance_ok and in_fvg_zone:
            print(f"✅ Bear imbalance + retrace найден для {symbol} [{interval}]")
            return True

        return False

    @staticmethod
    def determine_trend_ema(symbol: str, timeframe: str) -> str:
        """Функция для анализа тренда при помощи EMA100 и EMA50 + ADX
        :param symbol символ криптовалюты
        :param timeframe таймфрейм для анализа
        :return "Bull", "Bear", "Flat" """
        try:
            coin = TA_Handler(
                symbol=symbol,
                screener="crypto",
                exchange="Bybit",
                interval=timeframe,
                timeout=7
            )
            analysis = coin.get_analysis().indicators
            EMA50 = analysis['EMA50']
            EMA100 = analysis['EMA100']
            ADX = float(analysis['ADX'])
            ADX_PLUS_DI = float(analysis['ADX+DI'])
            ADX_MINUS_DI = float(analysis['ADX-DI'])
            # Определяем тренд на основе EMA
            if EMA50 > EMA100 and ADX > 25 and ADX_PLUS_DI > ADX_MINUS_DI:
                #print(f"Bull EMA50 {EMA50} EMA100 {EMA100} ADX {ADX} ADX_PLUS_DI {ADX_PLUS_DI} ADX_MINUS_DI {ADX_MINUS_DI}")
                return "Bull"  # Бычий тренд
            elif EMA50 < EMA100 and ADX > 25 and ADX_PLUS_DI < ADX_MINUS_DI:
                return "Bear"  # Медвежий тренд
            else:
                #print(f"Flat EMA50 {EMA50} EMA100 {EMA100} ADX {ADX} ADX_PLUS_DI {ADX_PLUS_DI} ADX_MINUS_DI {ADX_MINUS_DI}")
                return "Flat"  # Флэт (боковое движение)

        except Exception as e:
            print(f"⚠️ Ошибка при анализе {symbol} на {timeframe}: {e}")
            return False

    @staticmethod
    def detect_trend(symbol, timeframe, exchange_name="bybit", atr_period=14, lookback=100, threshold_factor=1.2, min_trend_change=0.01):
        try:
            # Инициализация биржи
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class()

            # Получение данных
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=lookback)
            df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])
            df["ts"] = pd.to_datetime(df["ts"], unit="ms")

            # Расчёт ATR
            df["atr"] = ta.atr(high=df["high"], low=df["low"], close=df["close"], length=atr_period)

            # Автоматическое определение порога волатильности
            volatility_threshold = df["atr"].median() * threshold_factor

            # Классификация режима
            df["regime"] = "Flat"
            df.loc[df["atr"] > volatility_threshold, "regime"] = "trend"

            # Последнее состояние
            last = df.iloc[-1]

            # Определение направления тренда
            trend = "Flat"
            price_change = (last["close"] - df["close"].iloc[-atr_period]) / df["close"].iloc[-atr_period]

            if last["regime"] == "trend" and abs(price_change) >= min_trend_change:
                trend = "Bull" if price_change > 0 else "Bear"

            # print(f"Последний режим рынка: {last['regime'].upper()} (ATR = {last['atr']:.2f}), Тренд: {trend}")
            #
            # return {
            #     "regime": last["regime"],
            #     "atr": last["atr"],
            #     "trend": trend,
            #     "price_change_pct": round(price_change * 100, 2)
            # }
            return trend

        except Exception as e:
            print(f"[detect_trend] Ошибка при получении данных: {e}")
            return None