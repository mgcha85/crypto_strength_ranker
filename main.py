from fetcher import fetch_binance_klines
from analyzer import compute_strength, compute_ohlcv_matrix_correlation, find_improved_symbols
from utils import load_config

def main():
    config = load_config()
    symbols = config["symbols"]
    intervals = config["intervals"]  # e.g. ["15m","5m","1m"]
    limit = config["limit"]
    improve_intervals = config.get("improve_intervals", intervals)

    # 1) 우선 15m 상관관계 필터링 (기존 로직)
    symbol_dfs = {}
    for symbol in symbols:
        try:
            df = fetch_binance_klines(symbol, "15m", limit)
            symbol_dfs[symbol] = df
        except Exception as e:
            print(f"❌ Failed to fetch {symbol} 15m: {e}")
    corr = compute_ohlcv_matrix_correlation(symbol_dfs, config["target"])
    corr_fi = {k: v for k, v in corr.items() if v > 0.4}

    # 2) 각 인터벌별 랭킹 계산
    rankings = {}
    for interval in intervals:
        print(f"\n📊 [Interval: {interval}]")
        dfs = {}
        for symbol in corr_fi:
            try:
                dfs[symbol] = fetch_binance_klines(symbol, interval, limit)
            except Exception as e:
                print(f"❌ Failed to fetch {symbol} {interval}: {e}")
        ranking = compute_strength(dfs)
        rankings[interval] = ranking
        # 기존 출력 유지
        for i, r in enumerate(ranking, start=1):
            print(f"{i:2d}. {r['symbol']:<8} | Return: {r['return']:.2%} "
                  f"| Disparity: {r['disparity']:.2%} | Score: {r['score']:.2%}")

    # 3) 15m→5m→1m 순으로 랭킹과 Score가 모두 개선된 심볼 찾기
    improved = find_improved_symbols(rankings, improve_intervals)
    if improved:
        seq = " → ".join(improve_intervals)
        print(f"\n▶ Symbols improved in order ({seq}):")
        for item in improved:
            s       = item['symbol']
            ranks   = "→".join(map(str, item['ranks']))
            scores  = "→".join(f"{v:.2%}" for v in item['scores'])
            print(f"- {s}: ranks {ranks}, scores {scores}")
    else:
        print("\n▶ No symbols found with both rank & score improvement.")


if __name__ == "__main__":
    main()
