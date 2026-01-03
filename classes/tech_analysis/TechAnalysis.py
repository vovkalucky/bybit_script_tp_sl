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
    def find_imbalance(cls, symbol: str, interval: str, limit: int = 10,
                       imbalance: float = 0.7, profit: float = 0.7) -> bool:
        """
        Функция поиска медвежьего имбаланса для сигнала BUY.

        Логика:
        - Ищем gap вниз между свечами (медвежий имбаланс)
        - Цена возвращается в зону имбаланса
        - Покупка с расчётом на закрытие gap'а

        Параметры:
        - imbalance: минимальный размер gap'а в процентах от цены
        - profit: минимальное расстояние текущей цены от верхней границы имбаланса (%)

        Структура свечей: [-4] = third, [-3] = second, [-2] = first, [-1] = current
        """
        klines = TechAnalysis.get_klines(symbol, interval, limit)

        if len(klines) < 4:
            print(f"[find_imbalance] Недостаточно данных для {symbol}")
            return False

        # Медвежий имбаланс: gap вниз, покупка на возврате в зону
        third_high = float(klines[-4][2])  # High третьей свечи
        third_close = float(klines[-4][4])  # Close третьей свечи
        second_low = float(klines[-3][3])  # Low второй свечи
        second_high = float(klines[-3][2])  # High второй свечи
        second_volume = float(klines[-3][5])  # Volume второй свечи (gap формирующая)
        first_low = float(klines[-2][3])  # Low первой свечи
        first_close = float(klines[-2][4])  # Close первой свечи
        first_volume = float(klines[-2][5])  # Volume первой свечи
        current_price = float(klines[-1][4])  # Текущая цена
        current_volume = float(klines[-1][5])  # Текущий объём

        # === ОСНОВНЫЕ УСЛОВИЯ ===

        # 1. Наличие gap'а (разрыва) между third и first свечой
        gap_exists = first_low < second_low < third_high

        # 2. Размер имбаланса (gap между high третьей и low первой)
        if third_high > 0:
            gap_size = (third_high - first_low) / third_high * 100
            condition_imbalance_size = gap_size > imbalance
        else:
            condition_imbalance_size = False

        # 3. Цена вернулась в зону имбаланса
        price_in_zone = first_low < current_price < third_high

        # 4. Потенциальная прибыль до верхней границы имбаланса
        if current_price > 0:
            potential_profit = (third_high - current_price) / current_price * 100
            condition_profit = potential_profit > profit
        else:
            condition_profit = False

        # 5. Вторая свеча формирует gap (находится внутри разрыва)
        condition_gap = second_high < third_high and second_low > first_low

        # === АНАЛИЗ ОБЪЁМА (ОПЦИОНАЛЬНО) ===

        # 6. Проверка объёма на свече формирования gap'а
        # Высокий объём на падении (вторая свеча) подтверждает сильное движение
        avg_volume = (second_volume + first_volume) / 2
        volume_spike = second_volume > avg_volume * 1.2  # Объём на 20% выше среднего

        # 7. Текущий объём не должен быть чрезмерно высоким (избегаем продолжения падения)
        current_volume_ok = current_volume < avg_volume * 1.5

        # === ДОПОЛНИТЕЛЬНЫЕ ФИЛЬТРЫ ===

        # 8. Импульсное движение вниз (подтверждение медвежьего имбаланса)
        if third_close > 0:
            price_drop = (third_close - first_close) / third_close * 100
            strong_movement = price_drop > imbalance * 0.5  # Падение минимум на 50% от размера gap'а
        else:
            strong_movement = False

        # === ФИНАЛЬНАЯ ПРОВЕРКА ===

        # Базовые условия (обязательные)
        basic_conditions = [gap_exists, condition_imbalance_size, price_in_zone,
                            condition_profit, condition_gap]

        # Условия с объёмом (рекомендуемые, но опциональные)
        volume_conditions = [volume_spike, current_volume_ok]

        # Вариант 1: Строгий (с объёмом)
        if all(basic_conditions + volume_conditions + [strong_movement]):
            print(f"✅ BEAR Imbalance [STRONG] [{symbol}] {interval}")
            print(f"   Gap: {gap_size:.2f}% | Profit potential: {potential_profit:.2f}%")
            print(f"   Zone: {first_low:.4f} - {third_high:.4f} | Current: {current_price:.4f}")
            print(f"   Volume: Gap={second_volume:.0f} | Avg={avg_volume:.0f} | Current={current_volume:.0f}")
            return True

        # # Вариант 2: Базовый (без объёма, но с сильным движением)
        # if all(basic_conditions + [strong_movement]):
        #     print(f"⚠️  BEAR Imbalance [MODERATE] [{symbol}] {interval}")
        #     print(f"   Gap: {gap_size:.2f}% | Profit potential: {potential_profit:.2f}%")
        #     print(f"   Zone: {first_low:.4f} - {third_high:.4f} | Current: {current_price:.4f}")
        #     print(f"   ⚠️  Volume conditions not met")
        #     return True  # Можно изменить на False, если хотите только сильные сигналы

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