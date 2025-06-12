import pandas as pd
import mplfinance as mpf

def plotalized_candlestick(df, symbol):
    df_plot = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'}).set_index('time')
    mpf.plot(df_plot, type='candle', title=f"{symbol} Normalized", style='charles')

def normalize_price(df):
    df = df.copy()

    base_open = df["open"].iloc[0]
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(lambda x: (x - base_open) / base_open + 1)
    return df

def compute_strength(symbol_dfs):
    strength = {}
    for symbol, df in symbol_dfs.items():
        df = normalize_price(df)
        # plotalized_candlestick(df, symbol)

        strength[symbol] = df["close"].iloc[-1] - 1  # 누적 수익률 %
    return sorted(strength.items(), key=lambda x: x[1], reverse=True)
