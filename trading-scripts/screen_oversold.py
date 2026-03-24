"""
screen_oversold.py

Screen tickers from major indices for oversold conditions:
  - Market cap >= --market-cap threshold
  - Weekly RSI (14-period) < 30
  - Current price < 100-week simple moving average

Usage:
  python screen_oversold.py --market-cap 2.8e12
"""

import argparse
import datetime
import hashlib
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf
from pytickersymbols import PyTickerSymbols
from tabulate import tabulate
from tqdm import tqdm

CACHE_DIR = Path.home() / ".cache" / "misc"
TZ_LA = ZoneInfo("America/Los_Angeles")


def get_universe() -> list[str]:
    pytickrs = PyTickerSymbols()
    spx = pytickrs.get_stocks_by_index("S&P 500")
    ndx = pytickrs.get_stocks_by_index("NASDAQ 100")
    dji = pytickrs.get_stocks_by_index("DOWN JONES")
    all_syms = []
    for ix in [spx, ndx, dji]:
        all_syms += [s["symbol"] for s in list(ix)]
    return sorted(list(set(all_syms)))


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = pd.Series(np.where(delta > 0, delta, 0), index=series.index)
    loss = pd.Series(np.where(delta < 0, -delta, 0), index=series.index)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _today_str() -> str:
    return datetime.datetime.now(TZ_LA).date().strftime("%Y%m%d")


def _cache_key(tag: str, symbols: list[str]) -> str:
    today = datetime.datetime.now(TZ_LA).date().isoformat()
    payload = "|".join([today, tag] + sorted(symbols))
    return f"{_today_str()}_{hashlib.sha256(payload.encode()).hexdigest()[:16]}"


def _load_or_write(cache_path: Path, fetch_fn) -> pd.DataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        print(f"  Cache hit: {cache_path}", flush=True)
        return pd.read_parquet(cache_path)
    df = fetch_fn()
    df.to_parquet(cache_path)
    print(f"  Cached to: {cache_path}", flush=True)
    return df


def _fetch_market_cap(s: str, retries: int = 3, backoff: float = 2.0) -> float | None:
    """Fetch market cap for a single ticker via fast_info, with retry on transient errors."""
    for attempt in range(retries):
        try:
            return yf.Ticker(s).fast_info["market_cap"]
        except Exception:
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    return None


def fetch_market_caps(symbols: list[str]) -> pd.DataFrame:
    """Return a DataFrame indexed by symbol with a marketCap column.
    Results are cached per day (LA time) keyed on the full universe."""
    key = _cache_key("mcap", symbols)
    cache_path = CACHE_DIR / f"{key}_yfinance.parquet"

    def fetch():
        rows = []
        for s in tqdm(symbols, desc="Fetching market caps", unit="ticker"):
            mc = _fetch_market_cap(s)
            rows.append({"symbol": s, "marketCap": mc})
        return pd.DataFrame(rows).set_index("symbol")

    return _load_or_write(cache_path, fetch)


def _download_chunk(
    chunk: list[str], period: str, interval: str, retries: int = 3, backoff: float = 2.0
) -> pd.DataFrame:
    """Download a single batch with retry. Always returns MultiIndex columns."""
    for attempt in range(retries):
        try:
            df = yf.download(
                chunk,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
            )
            # yf.download with a single-element list returns single-level columns;
            # normalise to MultiIndex so all chunks can be concatenated uniformly.
            if not isinstance(df.columns, pd.MultiIndex):
                df.columns = pd.MultiIndex.from_tuples(
                    [(col, chunk[0]) for col in df.columns]
                )
            return df
        except Exception:
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    return pd.DataFrame()


def _fetch_upside_potential(
    s: str, retries: int = 3, backoff: float = 2.0
) -> float | None:
    for attempt in range(retries):
        try:
            t = yf.Ticker(s).analyst_price_targets
            median, current = t.get("median"), t.get("current")
            if median and current and current != 0:
                return median / current
            return None
        except Exception:
            if attempt < retries - 1:
                time.sleep(backoff * (attempt + 1))
    return None


def fetch_upside_potentials(symbols: list[str]) -> pd.DataFrame:
    """Return a DataFrame indexed by symbol with an upsidePotential column.
    Results are cached per day (LA time) keyed on the qualifying symbol set."""
    key = _cache_key("analyst_targets", symbols)
    cache_path = CACHE_DIR / f"{key}_yfinance.parquet"

    def fetch():
        rows = []
        for s in tqdm(symbols, desc="Fetching analyst targets", unit="ticker"):
            rows.append({"symbol": s, "upsidePotential": _fetch_upside_potential(s)})
        return pd.DataFrame(rows).set_index("symbol")

    return _load_or_write(cache_path, fetch)


def fetch_prices(symbols: list[str], period: str, interval: str) -> pd.DataFrame:
    """Return a yfinance OHLCV DataFrame for symbols.
    Downloads in batches of 50 to avoid overwhelming yfinance's connection pool.
    Results are cached per day (LA time) keyed on the qualifying symbol set."""
    key = _cache_key(f"prices:{period}:{interval}", symbols)
    cache_path = CACHE_DIR / f"{key}_yfinance.parquet"

    def fetch():
        batch_size = 50
        chunks = [
            symbols[i : i + batch_size] for i in range(0, len(symbols), batch_size)
        ]
        frames = []
        for chunk in tqdm(chunks, desc="Downloading price batches", unit="batch"):
            df = _download_chunk(chunk, period, interval)
            if not df.empty:
                frames.append(df)
            time.sleep(0.5)
        return pd.concat(frames, axis=1) if frames else pd.DataFrame()

    return _load_or_write(cache_path, fetch)


def screen_tickers(market_cap_min: float) -> list[dict]:
    print("Loading symbol universe from major indices...", flush=True)
    symbols = get_universe()
    print(f"  {len(symbols)} symbols loaded", flush=True)

    print(f"Filtering by market cap >= {market_cap_min:.2e}...", flush=True)
    mcap_df = fetch_market_caps(symbols)
    qualifying = sorted(mcap_df[mcap_df["marketCap"] >= market_cap_min].index.tolist())
    print(f"  {len(qualifying)} symbols qualify", flush=True)

    if not qualifying:
        return []

    print(
        f"Fetching analyst price targets for {len(qualifying)} symbols...", flush=True
    )
    up_df = fetch_upside_potentials(qualifying)

    # Need 100w SMA + 14w RSI lookback; 10 years of weekly data is sufficient
    print(
        f"Downloading 10y weekly price data for {len(qualifying)} symbols...",
        flush=True,
    )
    df = fetch_prices(qualifying, period="10y", interval="1wk")

    # Normalise to a single-level column DataFrame keyed by symbol
    # yfinance returns MultiIndex columns (price_type, symbol) for multiple tickers
    if isinstance(df.columns, pd.MultiIndex):
        close_df = df["Close"]
    else:
        # Single ticker — wrap in a DataFrame so indexing is uniform
        close_df = df[["Close"]].rename(columns={"Close": qualifying[0]})

    results = []
    for s in qualifying:
        try:
            series = close_df[s].dropna()
            if len(series) < 114:  # 100w SMA + 14w RSI minimum
                continue

            sma_100w = series.rolling(window=100).mean()
            rsi_14w = calc_rsi(series, period=14)

            last_price = float(series.iloc[-1])
            last_sma = float(sma_100w.iloc[-1])
            last_rsi = float(rsi_14w.iloc[-1])

            if any(np.isnan(v) for v in [last_price, last_sma, last_rsi]):
                continue

            if last_rsi < 30 and last_price < last_sma:
                up = up_df.loc[s, "upsidePotential"] if s in up_df.index else None
                results.append(
                    {
                        "symbol": s,
                        "price": last_price,
                        "sma_100w": last_sma,
                        "delta_sma": last_sma - last_price,
                        "rsi_14w": last_rsi,
                        "upside_potential": float(up)
                        if up is not None
                        else float("nan"),
                    }
                )
        except Exception:
            pass

    return sorted(
        results,
        key=lambda x: x["upside_potential"]
        if not np.isnan(x["upside_potential"])
        else -np.inf,
        reverse=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Screen tickers with weekly RSI < 30 and price below 100w SMA"
    )
    parser.add_argument(
        "--market-cap",
        type=float,
        required=True,
        metavar="FLOAT",
        help="Minimum market cap in dollars (e.g. 2.8e12 for $2.8 trillion)",
    )
    args = parser.parse_args()

    results = screen_tickers(args.market_cap)

    if not results:
        print("\nNo tickers matched the criteria.")
        return

    headers = [
        "Symbol",
        "Price",
        "100w SMA",
        "$ Below SMA",
        "RSI (14w)",
        "Upside Potential",
    ]
    rows = [
        [
            r["symbol"],
            f"${r['price']:.2f}",
            f"${r['sma_100w']:.2f}",
            f"${r['delta_sma']:.2f}",
            f"{r['rsi_14w']:.4f}",
            f"+{(r['upside_potential'] - 1) * 100:.1f}%"
            if not np.isnan(r["upside_potential"])
            else "N/A",
        ]
        for r in results
    ]

    print()
    print(tabulate([headers] + rows, headers="firstrow"))
    print(f"\n{len(results)} ticker(s) matched.")


if __name__ == "__main__":
    main()
