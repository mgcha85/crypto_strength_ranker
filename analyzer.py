import pandas as pd
import mplfinance as mpf

def plotalized_candlestick(df, symbol):
    df_plot = df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'}).set_index('time')
    mpf.plot(df_plot, type='candle', title=f"{symbol} Normalized", style='charles')

def normalize_price(df):
    df = df.copy()
    base_open = df["open"].iloc[0]

    # 정규화된 가격 계산
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].apply(
        lambda x: (x - base_open) / base_open + 1
    )

    # SMA200 및 이격도 계산
    df["sma200"] = df["close"].rolling(window=200).mean()
    df["disparity_200"] = (df["close"] - df["sma200"]) / df["sma200"]

    return df

def compute_strength(symbol_dfs, weight_return=0.5, weight_disparity=0.5):
    results = []

    for symbol, df in symbol_dfs.items():
        df = normalize_price(df)

        # 누적 수익률
        cumulative_return = df["close"].iloc[-1] - 1

        # SMA200 이격도
        disparity_200 = df["disparity_200"].iloc[-1] if not pd.isna(df["disparity_200"].iloc[-1]) else 0

        # 통합 점수 (가중합)
        score = weight_return * cumulative_return + weight_disparity * disparity_200

        results.append({
            "symbol": symbol,
            "return": cumulative_return,
            "disparity": disparity_200,
            "score": score
        })

    # score 기준으로 정렬
    sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
    return sorted_results
