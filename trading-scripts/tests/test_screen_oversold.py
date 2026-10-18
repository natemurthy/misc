import datetime
import re
import sys

import numpy as np
import pandas as pd
import pytest

import screen_oversold as so


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    d = tmp_path / "cache"
    monkeypatch.setattr(so, "CACHE_DIR", d)
    return d


def weekly_index(n):
    return pd.date_range("2016-01-08", periods=n, freq="W-FRI")


# --- get_universe ---------------------------------------------------------------------------


def test_get_universe_is_sorted_deduped_and_contains_megacaps():
    syms = so.get_universe()
    assert syms == sorted(set(syms))
    assert {"AAPL", "MSFT"} <= set(syms)
    assert len(syms) > 400


# --- calc_rsi -------------------------------------------------------------------------------


def test_calc_rsi_saturates_for_monotone_series():
    rising = pd.Series(np.linspace(1, 50, 50), index=weekly_index(50))
    falling = pd.Series(np.linspace(50, 1, 50), index=weekly_index(50))
    assert so.calc_rsi(rising).iloc[-1] == 100.0
    assert so.calc_rsi(falling).iloc[-1] == 0.0


def test_calc_rsi_matches_manual_computation_and_keeps_index():
    rng = np.random.default_rng(3)
    s = pd.Series(100 + rng.normal(0, 1, 40).cumsum(), index=weekly_index(40))

    rsi = so.calc_rsi(s, period=14)

    assert rsi.index.equals(s.index)
    # np.where treats the leading NaN delta as 0 gain / 0 loss, so the 14-row window fills at index 13
    assert rsi.iloc[:13].isna().all()
    assert not np.isnan(rsi.iloc[13])
    deltas = np.diff(s.values)[-14:]
    avg_gain = np.where(deltas > 0, deltas, 0).mean()
    avg_loss = np.where(deltas < 0, -deltas, 0).mean()
    assert rsi.iloc[-1] == pytest.approx(100 - 100 / (1 + avg_gain / avg_loss))


# --- cache helpers --------------------------------------------------------------------------


def test_today_str_is_la_date_in_compact_form():
    assert re.fullmatch(r"\d{8}", so._today_str())
    assert so._today_str() == datetime.datetime.now(so.TZ_LA).date().strftime("%Y%m%d")


def test_cache_key_is_stable_order_insensitive_and_tag_sensitive():
    k1 = so._cache_key("mcap", ["B", "A"])
    k2 = so._cache_key("mcap", ["A", "B"])
    k3 = so._cache_key("prices", ["A", "B"])
    k4 = so._cache_key("mcap", ["A", "B", "C"])
    assert k1 == k2
    assert len({k1, k3, k4}) == 3
    assert re.fullmatch(rf"{so._today_str()}_[0-9a-f]{{16}}", k1)


def test_load_or_write_fetches_once_then_serves_parquet(cache_dir, capsys):
    calls = []
    path = cache_dir / "x.parquet"
    df = pd.DataFrame({"v": [1.0, 2.0]}, index=pd.Index(["A", "B"], name="symbol"))

    first = so._load_or_write(path, lambda: calls.append(1) or df)
    second = so._load_or_write(path, lambda: calls.append(2) or df)

    assert calls == [1]
    assert path.exists()
    pd.testing.assert_frame_equal(first, df)
    pd.testing.assert_frame_equal(second, df)
    out = capsys.readouterr().out
    assert "Cached to:" in out and "Cache hit:" in out


# --- single-ticker fetchers with retry ------------------------------------------------------


def _flaky_ticker(failures, result_attr, result):
    """yf.Ticker replacement that raises `failures` times then exposes `result_attr`."""
    state = {"calls": 0}

    class T:
        def __init__(self, sym):
            state["calls"] += 1
            state["sym"] = sym
            if state["calls"] <= failures:
                raise RuntimeError("transient")

        def __getattr__(self, name):
            if name == result_attr:
                return result
            raise AttributeError(name)

    return T, state


def test_fetch_market_cap_retries_with_linear_backoff(monkeypatch, no_sleep):
    T, state = _flaky_ticker(2, "fast_info", {"market_cap": 3.0e12})
    monkeypatch.setattr(so.yf, "Ticker", T)

    assert so._fetch_market_cap("AAPL") == 3.0e12
    assert state["calls"] == 3 and state["sym"] == "AAPL"
    assert no_sleep == [2.0, 4.0]


def test_fetch_market_cap_gives_up_after_retries(monkeypatch, no_sleep):
    T, state = _flaky_ticker(99, "fast_info", {})
    monkeypatch.setattr(so.yf, "Ticker", T)

    assert so._fetch_market_cap("AAPL", retries=2, backoff=0.5) is None
    assert state["calls"] == 2
    assert no_sleep == [0.5]  # no sleep after the final attempt


@pytest.mark.parametrize(
    "targets, expected",
    [
        ({"median": 110.0, "current": 100.0}, 1.1),
        ({"median": 110.0, "current": 0}, None),
        ({"median": None, "current": 100.0}, None),
        ({}, None),
    ],
)
def test_fetch_upside_potential(monkeypatch, no_sleep, targets, expected):
    T, _ = _flaky_ticker(0, "analyst_price_targets", targets)
    monkeypatch.setattr(so.yf, "Ticker", T)
    assert so._fetch_upside_potential("AAPL") == expected


def test_fetch_upside_potential_retries_then_returns_none(monkeypatch, no_sleep):
    T, state = _flaky_ticker(99, "analyst_price_targets", {})
    monkeypatch.setattr(so.yf, "Ticker", T)
    assert so._fetch_upside_potential("AAPL") is None
    assert state["calls"] == 3


# --- batch download -------------------------------------------------------------------------


def test_download_chunk_normalises_single_ticker_to_multiindex(monkeypatch, no_sleep):
    seen = {}
    flat = pd.DataFrame(
        {"Close": [1.0, 2.0], "Volume": [10, 20]}, index=weekly_index(2)
    )
    monkeypatch.setattr(
        so.yf,
        "download",
        lambda chunk, **kw: seen.update(chunk=chunk, **kw) or flat.copy(),
    )

    df = so._download_chunk(["AAPL"], "10y", "1wk")

    assert isinstance(df.columns, pd.MultiIndex)
    assert list(df.columns) == [("Close", "AAPL"), ("Volume", "AAPL")]
    assert seen == {
        "chunk": ["AAPL"],
        "period": "10y",
        "interval": "1wk",
        "auto_adjust": True,
        "progress": False,
    }


def test_download_chunk_leaves_multiindex_untouched(monkeypatch, no_sleep):
    cols = pd.MultiIndex.from_product([["Close"], ["A", "B"]])
    multi = pd.DataFrame([[1.0, 2.0]], index=weekly_index(1), columns=cols)
    monkeypatch.setattr(so.yf, "download", lambda chunk, **kw: multi)

    df = so._download_chunk(["A", "B"], "10y", "1wk")

    assert list(df.columns) == [("Close", "A"), ("Close", "B")]


def test_download_chunk_returns_empty_frame_after_exhausting_retries(
    monkeypatch, no_sleep
):
    def boom(*a, **k):
        raise RuntimeError("yfinance down")

    monkeypatch.setattr(so.yf, "download", boom)

    assert so._download_chunk(["A"], "10y", "1wk").empty
    assert no_sleep == [2.0, 4.0]


def test_fetch_prices_batches_fifty_at_a_time_and_concatenates(
    cache_dir, monkeypatch, no_sleep
):
    chunks = []

    def fake_chunk(chunk, period, interval):
        chunks.append(list(chunk))
        cols = pd.MultiIndex.from_product([["Close"], chunk])
        return pd.DataFrame(
            np.ones((3, len(chunk))), index=weekly_index(3), columns=cols
        )

    monkeypatch.setattr(so, "_download_chunk", fake_chunk)
    syms = [f"S{i:03d}" for i in range(120)]

    df = so.fetch_prices(syms, period="10y", interval="1wk")

    assert [len(c) for c in chunks] == [50, 50, 20]
    assert list(df["Close"].columns) == syms
    assert no_sleep == [0.5] * 3
    # second call is served from the parquet cache
    df2 = so.fetch_prices(syms, period="10y", interval="1wk")
    assert len(chunks) == 3
    assert df2.shape == df.shape


def test_fetch_market_caps_and_upside_potentials_index_by_symbol(
    cache_dir, monkeypatch
):
    monkeypatch.setattr(so, "_fetch_market_cap", lambda s: {"A": 1e12, "B": None}[s])
    monkeypatch.setattr(
        so, "_fetch_upside_potential", lambda s: {"A": 1.2, "B": None}[s]
    )

    mc = so.fetch_market_caps(["A", "B"])
    up = so.fetch_upside_potentials(["A", "B"])

    assert mc.index.tolist() == ["A", "B"] and mc.index.name == "symbol"
    assert mc.loc["A", "marketCap"] == 1e12 and np.isnan(mc.loc["B", "marketCap"])
    assert up.loc["A", "upsidePotential"] == 1.2 and np.isnan(
        up.loc["B", "upsidePotential"]
    )


# --- screen_tickers -------------------------------------------------------------------------


def _close_frame(series_by_symbol):
    """Build a MultiIndex (field, symbol) frame from {symbol: close values}; shorter series are NaN-padded."""
    n = max(len(v) for v in series_by_symbol.values())
    idx = weekly_index(n)
    cols = pd.MultiIndex.from_product([["Close"], list(series_by_symbol)])
    data = np.full((n, len(series_by_symbol)), np.nan)
    for j, v in enumerate(series_by_symbol.values()):
        data[n - len(v) :, j] = v
    return pd.DataFrame(data, index=idx, columns=cols)


@pytest.fixture
def screen_inputs(monkeypatch):
    """Universe of five names; only DOWN and DOWN2 should screen in."""
    falling = np.linspace(200, 80, 120)
    rising = np.linspace(80, 200, 120)
    monkeypatch.setattr(
        so, "get_universe", lambda: ["DOWN", "DOWN2", "UP", "SHORT", "SMALL"]
    )
    monkeypatch.setattr(
        so,
        "fetch_market_caps",
        lambda syms: pd.DataFrame(
            {"marketCap": [5e12, 4e12, 3e12, 2e12, 1e9]},
            index=pd.Index(syms, name="symbol"),
        ),
    )
    monkeypatch.setattr(
        so,
        "fetch_upside_potentials",
        lambda syms: pd.DataFrame(
            {"upsidePotential": [1.25 if s == "DOWN" else np.nan for s in syms]},
            index=pd.Index(syms, name="symbol"),
        ),
    )
    prices = _close_frame(
        {"DOWN": falling, "DOWN2": falling * 0.5, "UP": rising, "SHORT": falling[:50]}
    )
    seen = {}
    monkeypatch.setattr(
        so,
        "fetch_prices",
        lambda syms, period, interval: seen.update(
            syms=syms, period=period, interval=interval
        )
        or prices,
    )
    return seen


def test_screen_tickers_applies_cap_rsi_and_sma_filters(screen_inputs, capsys):
    results = so.screen_tickers(1e10)

    assert screen_inputs == {
        "syms": ["DOWN", "DOWN2", "SHORT", "UP"],
        "period": "10y",
        "interval": "1wk",
    }
    assert [r["symbol"] for r in results] == ["DOWN", "DOWN2"]  # NaN upside sorts last
    down = results[0]
    assert down["price"] == pytest.approx(80.0)
    assert down["sma_100w"] == pytest.approx(np.linspace(200, 80, 120)[-100:].mean())
    assert down["delta_sma"] == pytest.approx(down["sma_100w"] - 80.0)
    assert down["rsi_14w"] == 0.0
    assert down["upside_potential"] == 1.25
    assert np.isnan(results[1]["upside_potential"])
    assert "4 symbols qualify" in capsys.readouterr().out


def test_screen_tickers_returns_empty_when_nothing_meets_market_cap(screen_inputs):
    assert so.screen_tickers(1e13) == []


def test_screen_tickers_handles_single_level_columns_for_one_ticker(monkeypatch):
    falling = np.linspace(200, 80, 120)
    monkeypatch.setattr(so, "get_universe", lambda: ["DOWN"])
    monkeypatch.setattr(
        so,
        "fetch_market_caps",
        lambda syms: pd.DataFrame(
            {"marketCap": [5e12]}, index=pd.Index(syms, name="symbol")
        ),
    )
    monkeypatch.setattr(
        so,
        "fetch_upside_potentials",
        lambda syms: pd.DataFrame(
            {"upsidePotential": [1.1]}, index=pd.Index(syms, name="symbol")
        ),
    )
    monkeypatch.setattr(
        so,
        "fetch_prices",
        lambda *a, **k: pd.DataFrame(
            {"Close": falling, "Volume": 1.0}, index=weekly_index(120)
        ),
    )

    results = so.screen_tickers(1e10)

    assert [r["symbol"] for r in results] == ["DOWN"]
    assert results[0]["upside_potential"] == 1.1


# --- main -----------------------------------------------------------------------------------


def test_main_requires_market_cap_argument(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["screen_oversold.py"])
    with pytest.raises(SystemExit):
        so.main()


def test_main_prints_table_of_matches(monkeypatch, capsys):
    seen = {}
    rows = [
        {
            "symbol": "AAA",
            "price": 80.0,
            "sma_100w": 140.0,
            "delta_sma": 60.0,
            "rsi_14w": 12.3456,
            "upside_potential": 1.25,
        },
        {
            "symbol": "BBB",
            "price": 10.0,
            "sma_100w": 12.0,
            "delta_sma": 2.0,
            "rsi_14w": 28.0,
            "upside_potential": float("nan"),
        },
    ]
    monkeypatch.setattr(sys, "argv", ["screen_oversold.py", "--market-cap", "2.8e12"])
    monkeypatch.setattr(so, "screen_tickers", lambda cap: seen.update(cap=cap) or rows)

    so.main()

    out = capsys.readouterr().out
    assert seen == {"cap": 2.8e12}
    assert "2 ticker(s) matched." in out
    aaa = next(line for line in out.splitlines() if line.startswith("AAA"))
    assert aaa.split() == ["AAA", "$80.00", "$140.00", "$60.00", "12.3456", "+25.0%"]
    bbb = next(line for line in out.splitlines() if line.startswith("BBB"))
    assert bbb.split()[-1] == "N/A"


def test_main_reports_when_nothing_matches(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["screen_oversold.py", "--market-cap", "1e9"])
    monkeypatch.setattr(so, "screen_tickers", lambda cap: [])

    so.main()

    assert "No tickers matched the criteria." in capsys.readouterr().out
