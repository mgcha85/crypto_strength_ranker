from fetcher import fetch_binance_klines
from analyzer import compute_strength, compute_ohlcv_matrix_correlation
from utils import load_config

def main():
    config = load_config()
    symbols = config["symbols"]
    intervals = config["intervals"]
    limit = config["limit"]

    symbol_dfs = {}
    for symbol in symbols:
        try:
            df = fetch_binance_klines(symbol, "15m", limit)
            symbol_dfs[symbol] = df
        except Exception as e:
            print(f"❌ Failed to fetch {symbol}: {e}")
    
    corr = compute_ohlcv_matrix_correlation(symbol_dfs)
    corr_fi = {k: v for k, v in corr.items() if v > 0.7}
    corr_fo = {k: v for k, v in corr.items() if v < 0.7}
    print("filtered out: ", corr_fo)

    for interval in intervals:
        print(f"\n📊 [Interval: {interval}]")
        symbol_dfs = {}
        for symbol in corr_fi.keys():
            try:
                df = fetch_binance_klines(symbol, interval, limit)
                symbol_dfs[symbol] = df
            except Exception as e:
                print(f"❌ Failed to fetch {symbol}: {e}")
        
        ranking = compute_strength(symbol_dfs)
        for i, r in enumerate(ranking, 1):
            print(f"{i:2d}. {r['symbol']:<8} | Return: {r['return']:.2%} | Disparity: {r['disparity']:.2%} | Score: {r['score']:.2%}")


if __name__ == "__main__":
    main()
