#!/usr/bin/env python3
import sqlite3
from datetime import datetime
from fetcher import fetch_binance_klines
from analyzer import compute_strength, compute_ohlcv_matrix_correlation, find_improved_symbols
from utils import load_config

# DB 파일 경로
DB_PATH = "improved_signals.db"

def init_db(db_path: str = DB_PATH):
    """
    데이터베이스와 테이블이 없으면 생성합니다.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS improved_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_time TEXT NOT NULL,         -- 실행 시각 (ISO format)
            symbol TEXT NOT NULL,           -- 심볼 이름
            intervals TEXT NOT NULL,        -- 검사한 인터벌 순서 (콤마 구분)
            ranks TEXT NOT NULL,            -- 각 인터벌별 랭킹 (콤마 구분)
            scores TEXT NOT NULL            -- 각 인터벌별 Score (콤마 구분)
        )
    """)
    conn.commit()
    conn.close()

def save_improved(
    db_path: str,
    run_time: str,
    intervals: list[str],
    improved: list[dict]
):
    """
    improved 리스트를 DB에 저장합니다.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    intervals_str = ",".join(intervals)
    for item in improved:
        symbol = item["symbol"]
        ranks  = ",".join(map(str, item["ranks"]))
        # scores는 소수 형태로 저장
        scores = ",".join(f"{s:.6f}" for s in item["scores"])

        c.execute("""
            INSERT INTO improved_signals 
                (run_time, symbol, intervals, ranks, scores)
            VALUES (?, ?, ?, ?, ?)
        """, (run_time, symbol, intervals_str, ranks, scores))
    conn.commit()
    conn.close()

def main():
    # 0) DB 준비
    init_db()

    # 1) 설정 불러오기
    config = load_config()
    symbols           = config["symbols"]
    intervals         = config["intervals"]            # 예: ["15m","5m","1m"]
    improve_intervals = config.get("improve_intervals", intervals)
    limit             = config["limit"]
    target            = config["target"]               # 상관계산 대상, 예: "ETHUSDT"

    # 2) 상관관계 필터링 (15m 기준)
    symbol_dfs = {}
    for symbol in symbols:
        try:
            symbol_dfs[symbol] = fetch_binance_klines(symbol, "15m", limit)
        except Exception as e:
            print(f"❌ Failed to fetch {symbol} 15m: {e}")

    corr   = compute_ohlcv_matrix_correlation(symbol_dfs, target)
    corr_fi = [k for k,v in corr.items() if v > 0.4]

    # 3) 각 인터벌별 랭킹 계산
    rankings: dict[str, list[dict]] = {}
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

        # 기존 콘솔 출력
        for i, r in enumerate(ranking, start=1):
            print(f"{i:2d}. {r['symbol']:<8} | Return: {r['return']:.2%} "
                  f"| Disparity: {r['disparity']:.2%} | Score: {r['score']:.2%}")

    # 4) 랭킹&Score 개선 심볼 추출
    improved = find_improved_symbols(rankings, improve_intervals)

    # 5) DB에 저장
    run_time = datetime.utcnow().isoformat()
    if improved:
        save_improved(DB_PATH, run_time, improve_intervals, improved)
        print(f"\n▶ Saved {len(improved)} improved symbols at {run_time}")
    else:
        print("\n▶ No symbols improved—nothing saved to DB.")

if __name__ == "__main__":
    main()
