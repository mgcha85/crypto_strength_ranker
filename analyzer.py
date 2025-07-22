import numpy as np
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

def compute_ohlcv_matrix_correlation(symbol_dfs: dict[str, pd.DataFrame], target:str = "BTCUSDT") -> dict[str, float]:
    """
    For each symbol in symbol_dfs (excluding BTCUSDT), compute the Pearson correlation
    between the flattened BTCUSDT ohlcv data matrix and the flattened other symbol's ohlcv.
    Returns a dict: symbol -> correlation coefficient.
    """
    # Ensure BTC data exists
    if 'BTCUSDT' not in symbol_dfs:
        raise ValueError("BTCUSDT data required for matrix correlation")

    # Extract and align BTC data
    btc_df = symbol_dfs.pop(target)
    ohlc_col = ['open', 'high', 'low', 'close']
    btc_df = btc_df[ohlc_col].dropna()
    
    corrs = {}
    for sym, df in symbol_dfs.items():
        # Extract and align on timestamps
        other_df = df[ohlc_col].dropna()
        merged = pd.concat([btc_df, other_df], axis=1, keys=['btc','oth']).dropna()
        if merged.empty:
            corrs[sym] = np.nan
            continue
        
        # Flatten each matrix
        btc_mat = merged['btc'].to_numpy().ravel()
        oth_mat = merged['oth'].to_numpy().ravel()
        # Compute Pearson correlation
        corr = np.corrcoef(btc_mat, oth_mat)[0,1]
        corrs[sym] = float(corr)
    return corrs

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


def find_improved_symbols(rankings):
    """
    rankings: dict of { interval_str: [ { 'symbol', 'return', 'disparity', 'score' }, … ] }
    반환값: 15m→5m→1m 순으로 랭킹 위치가 내려가고(score는 올랐고) score도 연속 상승한 심볼 리스트
    """
    # symbol별로 각 인터벌의 rank, score 저장
    meta = {}
    for interval, ranking in rankings.items():
        for pos, r in enumerate(ranking, start=1):
            sym = r['symbol']
            d = meta.setdefault(sym, {})
            d[f'rank_{interval}'] = pos
            d[f'score_{interval}'] = r['score']

    result = []
    for sym, vals in meta.items():
        # 모든 인터벌 데이터가 있는지 확인
        if all(f'rank_{i}' in vals and f'score_{i}' in vals for i in ("15m","5m","1m")):
            r15, r5, r1 = vals['rank_15m'], vals['rank_5m'], vals['rank_1m']
            s15, s5, s1 = vals['score_15m'], vals['score_5m'], vals['score_1m']
            # 랭킹 위치가 좋아지고(score는 올랐다고 가정) 점수도 상승
            if (r15 > r5 > r1) and (s15 < s5 < s1):
                result.append({
                    'symbol': sym,
                    'ranks': (r15, r5, r1),
                    'scores': (s15, s5, s1),
                })
    return result

