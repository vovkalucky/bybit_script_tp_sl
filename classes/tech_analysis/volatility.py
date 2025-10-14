import ccxt
import pandas as pd
import ta
import matplotlib.pyplot as plt

symbol = 'BTC/USDT'
timeframe = '1d'
limit = 300

exchange = ccxt.bybit()
ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Расчёт ATR
df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()

# Классификация волатильности
q_low = df['atr'].quantile(0.33)
q_high = df['atr'].quantile(0.66)

def classify_volatility(x):
    if x < q_low:
        return 'Low'
    elif x < q_high:
        return 'Medium'
    else:
        return 'High'

df['vol_regime'] = df['atr'].apply(classify_volatility)
#print(df['vol_regime'])

# Визуализация
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['close'], label='Price', color='black')
colors = {'Low': 'green', 'Medium': 'orange', 'High': 'red'}
for regime, group in df.groupby('vol_regime'):
    plt.scatter(group['timestamp'], group['close'], label=regime, color=colors[regime], s=5)
plt.title('Volatility Regime Classification')
plt.legend()
plt.show()