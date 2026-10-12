import math

import numpy as np
import pandas as pd
import pytest

import pull_momentum_stats as pm


@pytest.fixture(autouse=True)
def reset_module_buffers():
    pm.results_stdout.clear()
    pm.results_dbwrite.clear()
    yield
    pm.results_stdout.clear()
    pm.results_dbwrite.clear()


def _walk(n, seed, start=100.0):
    rng = np.random.default_rng(seed)
    return start + rng.normal(0, 2, n).cumsum()


def single_symbol_frame(n=40):
    idx = pd.date_range("2025-03-01", periods=n, freq="B")
    close = _walk(n, 1)
    return pd.DataFrame(
        {
            "Close": close,
            "Adj Close": close * 0.99,
            "Low": close - 1.0,
            "High": close + 1.0,
        },
        index=idx,
    )


def multi_symbol_frame(syms, n=40):
    idx = pd.date_range("2025-03-01", periods=n, freq="B")
    cols = pd.MultiIndex.from_product(
        [["Close", "Low"], syms], names=["Price", "Ticker"]
    )
    data = np.column_stack(
        [_walk(n, i + 10) for i in range(len(syms))]
        + [_walk(n, i + 10) - 1 for i in range(len(syms))]
    )
    return pd.DataFrame(data, index=idx, columns=cols)


def reference_rsi(series: pd.Series, period=12) -> float:
    delta = series.diff()
    gain = pd.Series(np.where(delta > 0, delta, 0), index=series.index)
    loss = pd.Series(np.where(delta < 0, -delta, 0), index=series.index)
    rs = gain.rolling(period).mean() / loss.rolling(period).mean()
    return float((100 - 100 / (1 + rs)).iloc[-1])


# --- record -----------------------------------------------------------------------------------


def test_empty_result_is_all_nan_with_blank_period(fixed_today):
    m = pm.HistMomentumStat.empty_result("yfinance", "aapl")
    assert (
        m.symbol == "AAPL" and m.source == "yfinance" and m.trading_day == fixed_today
    )
    assert m.sma_period == ""
    for f in (
        "last_closing_price",
        "last_adj_close",
        "time_frame_low",
        "curr_distance_from_low",
        "last_sma",
        "last_rsi",
        "momentum_factor",
    ):
        assert math.isnan(getattr(m, f)), f


def test_write_rows_to_table_targets_timeseries_hist_momentum_stat(
    fake_db, fixed_today, capsys
):
    rows = [pm.HistMomentumStat.empty_result("yfinance", "a")]
    pm.write_rows_to_table(fake_db, rows)
    assert fake_db.inserts == [("timeseries", "hist_momentum_stat", rows)]
    assert "count=1, last_row_id=1" in capsys.readouterr().out


# --- pure helpers -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "period, days",
    [
        ("20d", 20),
        ("50d", 50),
        ("200d", 200),
        ("20w", 100),
        ("200w", 1000),
        ("", 20),
        ("bogus", 20),
    ],
)
def test_days_in_window(period, days):
    assert pm.days_in_window(period) == days


def test_calc_sma_returns_last_five_rolling_means():
    s = pd.Series(np.arange(1.0, 31.0))
    out = pm.calc_sma(s, "5d")
    assert len(out) == 5
    assert out.iloc[-1] == pytest.approx(s.tail(5).mean())
    assert out.iloc[0] == pytest.approx(s.iloc[21:26].mean())


def test_calc_sma_is_nan_when_window_exceeds_history():
    out = pm.calc_sma(pd.Series(np.arange(10.0)), "20d")
    assert out.isna().all()


def test_calc_rsi_matches_reference_formula_on_datetime_indexed_series():
    s = pd.Series(_walk(40, 7), index=pd.date_range("2025-01-01", periods=40, freq="B"))
    out = pm.calc_rsi(s)
    assert len(out) == 5
    assert out.iloc[-1] == pytest.approx(reference_rsi(s))
    assert out.iloc[0] == pytest.approx(reference_rsi(s.iloc[:-4]))


def test_calc_rsi_saturates_for_monotone_series():
    rising = pd.Series(np.linspace(100, 130, 30))
    falling = pd.Series(np.linspace(130, 100, 30))
    assert pm.calc_rsi(rising).tolist() == [100.0] * 5
    assert pm.calc_rsi(falling).tolist() == [0.0] * 5


def test_get_time_frame_low():
    assert pm.get_time_frame_low(pd.Series([3.0, 1.5, 2.0])) == 1.5


@pytest.mark.parametrize(
    "index, period",
    [
        ("0", "20d"),
        ("1", "50d"),
        ("2", "100d"),
        ("3", "200d"),
        ("4", "20w"),
        ("5", "50w"),
        ("6", "100w"),
        ("7", "200w"),
        ("8", ""),
    ],
)
def test_get_sma_period_from_task_index(monkeypatch, index, period):
    monkeypatch.setenv("CLOUD_RUN_TASK_INDEX", index)
    assert pm.get_sma_period_from_task_index() == period


def test_get_sma_period_defaults_to_20d_outside_cloud_run(monkeypatch):
    monkeypatch.delenv("CLOUD_RUN_TASK_INDEX", raising=False)
    assert pm.get_sma_period_from_task_index() == "20d"


# --- get_momentum_stats -----------------------------------------------------------------------


def test_get_momentum_stats_single_symbol_prints_summary(fake_db, capsys):
    df = single_symbol_frame()
    close = df["Close"]
    last, low = float(close.iloc[-1]), float(df["Low"].min())
    sma = float(close.rolling(20).mean().iloc[-1])

    pm.get_momentum_stats(["AAA"], "20d", df, fake_db)

    out = capsys.readouterr().out
    assert (
        f"Last price: $ last {last:.5f}, adj_close {df['Adj Close'].iloc[-1]:.5f}"
        in out
    )
    assert f"Time frame low: {low:.5f}" in out
    assert f"Current distance from low: {(last - low) / low * 100:.2f} %" in out
    assert f"Current 20d SMA: ${sma:.5f}" in out
    assert f"Current RSI: {reference_rsi(close):.5f}" in out
    assert f"Upside momentum: {sma / last:.5f}" in out
    assert pm.results_stdout == {} and pm.results_dbwrite == []


def test_get_momentum_stats_multi_symbol_dry_run_prints_factor_per_symbol(
    fake_db, fixed_today, capsys
):
    syms = ["AAA", "BBB"]
    df = multi_symbol_frame(syms)

    pm.get_momentum_stats(syms, "20d", df, fake_db, write_to_db=False)

    out = capsys.readouterr().out
    for s in syms:
        close = df["Close"][s]
        expected = float(close.rolling(20).mean().iloc[-1]) / float(close.iloc[-1])
        assert pm.results_stdout[s] == pytest.approx(expected)
        assert f"{s} {expected:.2f}" in out
    assert pm.results_dbwrite == []
    assert fake_db.inserts == []


def test_get_momentum_stats_multi_symbol_buffers_full_records_for_db(
    fake_db, fixed_today
):
    syms = ["AAA", "BBB"]
    df = multi_symbol_frame(syms)

    pm.get_momentum_stats(syms, "20d", df, fake_db, write_to_db=True)

    assert [m.symbol for m in pm.results_dbwrite] == syms
    m = pm.results_dbwrite[0]
    close = df["Close"]["AAA"]
    last, low = float(close.iloc[-1]), float(close.min())
    sma = float(close.rolling(20).mean().iloc[-1])
    assert (
        m.source == "yfinance"
        and m.trading_day == fixed_today
        and m.sma_period == "20d"
    )
    assert m.last_closing_price == last
    assert m.time_frame_low == low  # low is taken from Close, not Low
    assert m.curr_distance_from_low == pytest.approx((last - low) / low * 100)
    assert m.last_sma == pytest.approx(sma)
    assert m.last_rsi == pytest.approx(reference_rsi(close))
    assert m.momentum_factor == pytest.approx(sma / last)
    assert math.isnan(m.last_adj_close)


def test_get_momentum_stats_only_records_rsi_for_20d_period(fake_db, fixed_today):
    syms = ["AAA"]
    pm.get_momentum_stats(
        syms, "50d", multi_symbol_frame(syms, n=80), fake_db, write_to_db=True
    )
    assert pm.results_dbwrite[0].sma_period == "50d"
    assert math.isnan(pm.results_dbwrite[0].last_rsi)


def test_get_momentum_stats_skips_symbols_with_insufficient_history(
    fake_db, fixed_today
):
    syms = ["AAA"]
    pm.get_momentum_stats(
        syms, "200d", multi_symbol_frame(syms, n=40), fake_db, write_to_db=True
    )
    assert pm.results_dbwrite == [] and pm.results_stdout == {}


def test_get_momentum_stats_flushes_periodically_once_buffer_exceeds_ten(
    fake_db, fixed_today, monkeypatch, capsys
):
    monkeypatch.setattr(pm.random, "randint", lambda a, b: 3)
    syms = [f"S{i:02d}" for i in range(15)]

    pm.get_momentum_stats(
        syms, "20d", multi_symbol_frame(syms), fake_db, write_to_db=True
    )

    # buffer exceeds 10 after index 10; next index divisible by 3 is 12 -> flush 12, leave 3
    assert [len(rows) for _, _, rows in fake_db.inserts] == [12]
    assert [m.symbol for m in pm.results_dbwrite] == syms[12:]
    assert "Progress: 12 of 15" in capsys.readouterr().out


# --- main -------------------------------------------------------------------------------------


@pytest.fixture
def downloader(monkeypatch):
    seen = {}

    def fake(symbols, start, end):
        seen.update(symbols=symbols, start=start, end=end)
        # 80 rows covers the 50d window used by the CLOUD_RUN_TASK_INDEX=1 test below
        return (
            single_symbol_frame()
            if len(symbols) == 1
            else multi_symbol_frame(symbols, n=80)
        )

    monkeypatch.setattr(pm, "download_yf_data", fake)
    return seen


def test_main_multi_symbol_requests_window_sized_to_sma_period(
    downloader, fake_db, fixed_today, symbols, argv, monkeypatch, capsys
):
    monkeypatch.setenv(
        "CLOUD_RUN_TASK_INDEX", "1"
    )  # -> 50d -> 75 calendar days of history
    symbols(["AAA", "BBB"])
    argv("my_sorted_symbols.txt")

    pm.main()

    out = capsys.readouterr().out
    assert downloader == {
        "symbols": ["AAA", "BBB"],
        "start": "2025-02-22",
        "end": "2025-05-08",
    }
    assert "sma_period = 50d" in out
    assert "Momentum Factor" in out
    assert fake_db.connected is False
    assert sorted(pm.results_stdout) == ["AAA", "BBB"]


def test_main_multi_symbol_table_is_sorted_descending(
    downloader, fake_db, fixed_today, symbols, argv, monkeypatch, capsys
):
    monkeypatch.delenv("CLOUD_RUN_TASK_INDEX", raising=False)
    symbols(["AAA", "BBB", "CCC"])
    argv("my_sorted_symbols.txt")

    pm.main()

    out = capsys.readouterr().out
    table = out[out.index("Momentum Factor") :]
    rows = [line.split() for line in table.splitlines()[2:] if line.strip()]
    factors = [float(v) for _, v in rows]
    assert factors == sorted(factors, reverse=True)
    assert {s for s, _ in rows} == {"AAA", "BBB", "CCC"}


def test_main_multi_symbol_dry_run_false_connects_and_flushes(
    downloader, fake_db, fixed_today, symbols, argv, monkeypatch
):
    monkeypatch.delenv("CLOUD_RUN_TASK_INDEX", raising=False)
    symbols(["AAA", "BBB"])
    argv("my_sorted_symbols.txt", "--dry-run=false")

    pm.main()

    assert fake_db.connected is True
    assert [t[:2] for t in fake_db.inserts] == [("timeseries", "hist_momentum_stat")]
    assert [m.symbol for m in fake_db.rows] == ["AAA", "BBB"]


def test_main_single_symbol_never_writes(
    downloader, fake_db, fixed_today, symbols, argv, monkeypatch, capsys
):
    monkeypatch.delenv("CLOUD_RUN_TASK_INDEX", raising=False)
    symbols(["AAA"])
    argv("AAA", "--dry-run=false")

    pm.main()

    assert downloader["symbols"] == ["AAA"]
    assert fake_db.inserts == []
    assert "Upside momentum:" in capsys.readouterr().out


def test_download_yf_data_delegates_to_yfinance_and_echoes_last_date(
    monkeypatch, capsys
):
    seen = {}

    def fake_download(symbols, start, end):
        seen.update(symbols=symbols, start=start, end=end)
        return single_symbol_frame(5)

    monkeypatch.setattr(pm.yf, "download", fake_download)

    df = pm.download_yf_data(["AAA"], "2025-01-01", "2025-02-01")

    assert seen == {"symbols": ["AAA"], "start": "2025-01-01", "end": "2025-02-01"}
    assert len(df) == 5
    assert f"Last price date: {df.index[-1]}" in capsys.readouterr().out
