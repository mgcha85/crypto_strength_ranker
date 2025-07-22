import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

def fetch_binance_klines(symbol, interval, limit=200):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "n_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["time"] = pd.to_datetime(df["open_time"], unit="ms").dt.tz_localize("UTC").dt.tz_convert(KST)
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    return df[["time", "open", "high", "low", "close"]]
