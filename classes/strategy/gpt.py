import time
import pandas_ta as ta
import pandas as pd
from pybit.unified_trading import HTTP


# === Настройки API (ключи нужны только для торговли, PUBLIC DATA не требует ключей) ===
client = HTTP(testnet=False)




class AnalysisCoin:
    def __init__(self, pair, timeframe="15", limit=2000):
        self.pair = pair
        self.timeframe = timeframe
        self.limit = limit

    def get_historical_data(self) -> pd.DataFrame:
        try:
            response = client.get_kline(
                category="spot",
                symbol=self.pair,
                interval=self.timeframe,
                limit=self.limit
            )

            data = response["result"]["list"]
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(
                data,
                columns=[
                    "open_time", "open", "high", "low",
                    "close", "volume", "turnover"
                ]
            )

            df["open_time"] = pd.to_datetime(
                pd.to_numeric(df["open_time"], errors="coerce"),
                unit="ms"
            )

            df.set_index("open_time", inplace=True)
            df = df.astype(float)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            print(f"[Bybit ERROR] {self.pair}: {e}")
            return pd.DataFrame()

    def analyze_coin(self) -> str:
        df = self.get_historical_data()

        if df.empty or len(df) < 50:
            return "Wait"

        # === Indicators ===
        df["rsi"] = ta.rsi(df["close"], length=14)

        bb = ta.bbands(df["close"], length=20, std=2)
        df["bb_lower"] = bb.iloc[:, 0]

        macd = ta.macd(df["close"])
        df["macd_hist"] = macd.iloc[:, 2]

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # === УСЛОВИЯ (адаптированы под intraday) ===
        rsi_ok = last["rsi"] < 42
        bb_ok = last["close"] <= last["bb_lower"] * 1.01
        macd_ok = last["macd_hist"] > prev["macd_hist"]

        if rsi_ok and bb_ok:
            return "Buy"

        return "Wait"



