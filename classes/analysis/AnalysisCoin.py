from tradingview_ta import TA_Handler, Interval

TIMEFRAMES = {
    "1m": {
        "interval": Interval.INTERVAL_1_MINUTE,
        "indicators": ["RSI", "W%R", "Stoch.RSI", "MACD", "BBP"],
        "min_signal_count": 2
    },
    "5m": {
        "interval": Interval.INTERVAL_5_MINUTES,
        "indicators": ["RSI", "STOCH.K", "Mom", "ADX", "AO"],
        "min_signal_count": 2
    }
}

class AnalysisCoin:
    def __init__(self, pair):
        self.pair = pair

    def analyze_with_indicators(self, timeframe: str, indicators: [], min_signal_count: int, signal_type: str) -> bool:
        try:
            coin = TA_Handler(
                symbol=self.pair,
                screener="crypto",
                exchange="Bybit",
                interval=timeframe,
                timeout=7
            )
            analysis = coin.get_analysis().oscillators
            compute = analysis['COMPUTE']

            matching_signals = sum(
                1 for indicator, status in compute.items()
                if indicator in indicators and status == signal_type
            )

            return matching_signals >= min_signal_count
        except Exception as e:
            print(f"⚠️ Ошибка при анализе {self.pair} на {timeframe}: {e}")
            return False

    def has_trade_signal(self) -> bool:
        for tf_name, tf_data in TIMEFRAMES.items():
            for signal_type in ["BUY"]:
                is_signal = self.analyze_with_indicators(
                    timeframe=tf_data["interval"],
                    indicators=tf_data["indicators"],
                    min_signal_count=tf_data["min_signal_count"],
                    signal_type=signal_type
                )
                if not is_signal:
                    #print(f"🔴 Сигнал для {self.pair} не найден!")
                    return False
        return True
