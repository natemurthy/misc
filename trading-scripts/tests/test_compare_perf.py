import numpy as np
import pandas as pd
import pytest

import compare_perf as cp

SYMBOLS = ["SPY", "QQQ", "TSLA"]


def _bench_download_frame():
    """Mimic yf.download(...): MultiIndex columns (field, symbol), business-day index with a
    weekend gap (Fri 2024-01-05 -> Mon 2024-01-08) so resample('D').ffill() has work to do."""
    idx = pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-08"])
    close = pd.DataFrame(
        {
            "SPY": [100.0, 110.0, 121.0],
            "QQQ": [50.0, 45.0, 60.0],
            "TSLA": [200.0, 200.0, 100.0],
        },
        index=idx,
    )
    cols = pd.MultiIndex.from_product([["Close"], SYMBOLS])
    df = pd.DataFrame(close[SYMBOLS].values, index=idx, columns=cols)
    return df


# --- get_bench_data -------------------------------------------------------------------------


def test_get_bench_data_requests_2024_calendar_year_for_benchmarks(monkeypatch):
    calls = {}

    def fake_download(symbols, start, end):
        calls.update(symbols=symbols, start=start, end=end)
        return _bench_download_frame()

    monkeypatch.setattr(cp.yf, "download", fake_download)

    cp.get_bench_data()

    assert calls == {"symbols": SYMBOLS, "start": "2024-01-01", "end": "2025-01-01"}


def test_get_bench_data_forward_fills_weekend_and_computes_pct_from_first_close(
    monkeypatch,
):
    monkeypatch.setattr(cp.yf, "download", lambda *a, **k: _bench_download_frame())

    df = cp.get_bench_data()

    # 2024-01-04 .. 2024-01-08 inclusive is 5 calendar days after daily resample
    assert len(df) == 5
    assert df.index.tz is None
    # Weekend rows carry Friday's close forward
    sat = pd.Timestamp("2024-01-06")
    assert df.at[sat, "SPY"] == 110.0
    assert df.at[sat, "diff_SPY"] == pytest.approx(10.0)
    # First row is the baseline (0 %), last row is relative to the first close
    assert df["diff_SPY"].iloc[0] == 0.0
    assert df["diff_SPY"].iloc[-1] == pytest.approx(21.0)
    assert df["diff_QQQ"].iloc[-1] == pytest.approx(20.0)
    assert df["diff_TSLA"].iloc[-1] == pytest.approx(-50.0)
    assert set(df.columns) == set(SYMBOLS) | {f"diff_{s}" for s in SYMBOLS}


# --- get_nate_data --------------------------------------------------------------------------


def _nate_csv_frame():
    return pd.DataFrame(
        {
            "Date (EOD)": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "Total Value": ["$1,000.00", "$1,200.00", "$900.50"],
            "Invested Capital": ["$500", "$600", "$500"],
            "Notes": ["", "deposit", ""],
        }
    )


def test_get_nate_data_reads_the_downloads_export(monkeypatch):
    seen = {}

    def fake_read_csv(path, *a, **k):
        seen["path"] = path
        return _nate_csv_frame()

    monkeypatch.setattr(cp.pd, "read_csv", fake_read_csv)

    cp.get_nate_data()

    assert seen["path"] == "/Users/nathan/Downloads/2024_invest_perf_nate.csv"


def test_get_nate_data_strips_currency_and_measures_return_net_of_new_capital(
    monkeypatch,
):
    monkeypatch.setattr(cp.pd, "read_csv", lambda *a, **k: _nate_csv_frame())

    df = cp.get_nate_data()

    assert list(df.columns) == ["Total Value", "Invested Capital", "diff"]
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.name == "Date (EOD)"
    assert df["Total Value"].tolist() == [1000.0, 1200.0, 900.5]
    # Invested capital is re-based to the first row
    assert df["Invested Capital"].tolist() == [0.0, 100.0, 0.0]
    # diff = (value - net new capital - starting value) / starting value * 100
    assert df["diff"].iloc[0] == 0.0
    assert df["diff"].iloc[1] == pytest.approx((1200 - 100 - 1000) / 1000 * 100)
    assert df["diff"].iloc[2] == pytest.approx((900.5 - 0 - 1000) / 1000 * 100)


# --- export_diffs ---------------------------------------------------------------------------


def test_export_diffs_keeps_only_pct_columns_renamed_and_writes_csv(workdir):
    idx = pd.to_datetime(["2024-01-01", "2024-01-02"])
    bench = pd.DataFrame(
        {
            "SPY": [1, 2],
            "QQQ": [1, 2],
            "TSLA": [1, 2],
            "diff_SPY": [0.0, 1.5],
            "diff_QQQ": [0.0, 2.5],
            "diff_TSLA": [0.0, -1.0],
        },
        index=idx,
    )
    nate = pd.DataFrame(
        {"Total Value": [10, 11], "Invested Capital": [0, 0], "diff": [0.0, 10.0]},
        index=idx,
    )

    perf = cp.export_diffs(bench, nate)

    assert list(perf.columns) == ["SPY", "QQQ", "TSLA", "Nate"]
    assert perf["Nate"].tolist() == [0.0, 10.0]
    assert perf["SPY"].tolist() == [0.0, 1.5]
    written = pd.read_csv(
        workdir / "2024_invest_perf.csv", index_col=0, parse_dates=True
    )
    pd.testing.assert_frame_equal(written, perf, check_names=False, check_freq=False)


def test_export_diffs_outer_joins_on_date(workdir):
    bench = pd.DataFrame(
        {
            "SPY": [1],
            "QQQ": [1],
            "TSLA": [1],
            "diff_SPY": [0.0],
            "diff_QQQ": [0.0],
            "diff_TSLA": [0.0],
        },
        index=pd.to_datetime(["2024-01-01"]),
    )
    nate = pd.DataFrame(
        {"Total Value": [1], "Invested Capital": [0], "diff": [5.0]},
        index=pd.to_datetime(["2024-01-02"]),
    )

    perf = cp.export_diffs(bench, nate)

    assert len(perf) == 2
    assert np.isnan(perf.at[pd.Timestamp("2024-01-02"), "SPY"])
    assert perf.at[pd.Timestamp("2024-01-02"), "Nate"] == 5.0


# --- main -----------------------------------------------------------------------------------


def test_main_wires_bench_and_nate_frames_into_export(monkeypatch, capsys):
    bench, nate = object(), object()
    perf = pd.DataFrame({"SPY": [1.0], "Nate": [2.0]})
    calls = []

    monkeypatch.setattr(cp, "get_bench_data", lambda: bench)
    monkeypatch.setattr(cp, "get_nate_data", lambda: nate)
    monkeypatch.setattr(cp, "export_diffs", lambda a, b: calls.append((a, b)) or perf)

    cp.main()

    assert calls == [(bench, nate)]
    assert "Nate" in capsys.readouterr().out
