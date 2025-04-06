from typing import List
from pybit.unified_trading import HTTP
from tradingview_ta import TA_Handler, Interval

from config import BYBIT_API_KEY, BYBIT_SECRET_KEY
from settings import DEMO_TRADE


class TechAnalysis:
    session = HTTP(api_key=BYBIT_API_KEY,
                   api_secret=BYBIT_SECRET_KEY,
                   demo=DEMO_TRADE,
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
    def find_imbalance(cls, symbol: str, interval: str, direction: str, limit: int = 10, imbalance: float = 0.7,
                       profit: float = 0.7) -> bool:
        """Функция поиска имбаланса. Определяет бычий (Bull) или медвежий (Bear) дисбаланс.
        Для анализа берутся три последние закрытые свечи и текущая (current_kline) для входа в сделку.
        Параметры:
        - direction: "bull" для бычьего или "bear" для медвежьего имбаланса
        - imbalance: минимальный размер тела свечи в процентах
        - profit: минимальная ожидаемая прибыль в процентах
        """
        klines = TechAnalysis.get_klines(symbol, interval, limit)

        if direction == "bear":
            third_imb_kline = float(klines[-4][3])  # low
            second_imb_kline = float(klines[-3][3])  # low
            first_imb_kline = float(klines[-2][2])  # high
            current_kline = float(klines[-1][4])  # current_price

            condition_0 = second_imb_kline < third_imb_kline
            condition_1 = (first_imb_kline - current_kline) / first_imb_kline > profit / 100
            condition_2 = (third_imb_kline - first_imb_kline) / third_imb_kline > imbalance / 100
            signal = "Buy"
        elif direction == "bull":
            third_imb_kline = float(klines[-4][2])  # high
            second_imb_kline = float(klines[-3][2])  # high
            first_imb_kline = float(klines[-2][3])  # low
            current_kline = float(klines[-1][4])  # current_price

            condition_0 = second_imb_kline > third_imb_kline
            condition_1 = (current_kline - first_imb_kline) / first_imb_kline > profit / 100
            condition_2 = (first_imb_kline - third_imb_kline) / third_imb_kline > imbalance / 100
            signal = "Sell"
        else:
            print(f"[find_imbalance] Invalid direction: {direction}")
            return "No signal"

        if all([condition_0, condition_1, condition_2]):
            print(f"✅✅✅✅✅✅✅✅ {direction.capitalize()} Imbalance for {symbol} in {interval} found! ✅✅✅✅✅✅✅✅")
            return True
        else:
            return "No signal"

    # @classmethod
    # def find_bear_imbalance(cls, symbol: str, interval:str, limit: int = 10, imbalance: float = 0.5, profit: float = 1) -> str:
    #     """Функция поиска медвежьего имбаланса - падающие свечи. Для анализа берутся
    #     три последние закрытые свечи и текущая (current_kline) для входа в сделку. Размер имбаланса по умолчанию
    #     (imbalance)- 0.5%, текущая цена ниже нижней границы имбаланса на 1%, т.е. цена вернется в эту зону (profit)"""
    #     klines = TechAnalysis.get_klines(symbol, interval, limit)
    #     third_imb_kline = float(klines[-4][3]) #low
    #     second_imb_kline = float(klines[-3][3]) #low
    #     first_imb_kline = float(klines[-2][2]) #high
    #     current_kline = float(klines[-1][4]) #current_price
    #
    #     condition_0 = second_imb_kline < third_imb_kline
    #     condition_1 = (first_imb_kline - current_kline)/first_imb_kline > profit/100 # для входа в сделку чтобы прибыль составила profit (%)
    #     condition_2 = (third_imb_kline - first_imb_kline)/third_imb_kline > imbalance/100 # размера тела падающей свечи более imbalance (%)
    #
    #     list_of_conditions = [condition_0, condition_1, condition_2]
    #     if all(list_of_conditions):
    #     #if all([True]):
    #         print(f"✅✅✅✅✅✅✅✅ Bear Imbalance for {symbol} in {interval} find! ✅✅✅✅✅✅✅✅")
    #         return "Buy"
    #     else:
    #         return "No buy"
    #
    # @classmethod
    # def find_bull_imbalance(cls, symbol: str, interval: str, limit: int = 10, imbalance: float = 0.5, profit: float = 0.5) -> str:
    #     """Функция поиска бычьего имбаланса - растущие свечи. Для анализа берутся
    #     три последние закрытые свечи и текущая (current_kline) для входа в сделку. Размер имбаланса по умолчанию
    #     (imbalance)- 0.5%, текущая цена ниже нижней границы имбаланса на 1%, т.е. цена вернется в эту зону (profit)"""
    #     klines = TechAnalysis.get_klines(symbol, interval, limit)
    #     third_imb_kline = float(klines[-4][2])  # high
    #     second_imb_kline = float(klines[-3][2])  # high
    #     first_imb_kline = float(klines[-2][3])  # low
    #     current_kline = float(klines[-1][4])  # current_price
    #
    #     condition_0 = second_imb_kline > third_imb_kline
    #     condition_1 = (current_kline - first_imb_kline) / first_imb_kline > profit / 100  # условие для входа в сделку, чтобы прибыль составила profit (%)
    #     condition_2 = (first_imb_kline - third_imb_kline) / third_imb_kline > imbalance / 100  # размер тела растущей свечи более imbalance (%)
    #     list_of_conditions = [condition_0, condition_1, condition_2]
    #     #print(f"{symbol} {list_of_conditions}")
    #     if all(list_of_conditions):
    #         print(f"✅✅✅✅✅✅✅✅ Bull Imbalance for {symbol} in {interval} found! ✅✅✅✅✅✅✅✅")
    #         return "Sell"
    #     else:
    #         return "No Sell"


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





