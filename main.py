from fetcher import fetch_binance_klines
from analyzer import compute_strength
from utils import load_config

def main():
    config = load_config()
    symbols = config["symbols"]
    intervals = config["intervals"]
    limit = config["limit"]

    for interval in intervals:
        print(f"\n📊 [Interval: {interval}]")
        symbol_dfs = {}
        for symbol in symbols:
            try:
                df = fetch_binance_klines(symbol, interval, limit)
                symbol_dfs[symbol] = df
            except Exception as e:
                print(f"❌ Failed to fetch {symbol}: {e}")
        
        ranking = compute_strength(symbol_dfs)
        for rank, (symbol, strength) in enumerate(ranking, start=1):
            print(f"{rank:2d}. {symbol}: {strength:.2%}")


if __name__ == "__main__":
    main()
