import math

import pytest

import pull_dividend_yields as pdy


class _Resp:
    def __init__(self, text):
        self.text = text


def _ticker_factory(info, seen=None):
    """Build a yf.Ticker replacement whose .info is a fixed dict (or raises if info is an Exception)."""

    class T:
        def __init__(self, sym):
            if seen is not None:
                seen.append(sym)

        @property
        def info(self):
            if isinstance(info, Exception):
                raise info
            return info

    return T


# --- HistDividendYieldRecord ----------------------------------------------------------------


def test_empty_result_has_nan_rate_and_price(fixed_today):
    r = pdy.HistDividendYieldRecord.empty_result("yfinance", "vz")

    assert (r.id, r.created_at) == (None, None)
    assert r.source == "yfinance"
    assert r.symbol == "VZ"
    assert r.trading_day == fixed_today
    assert math.isnan(r.rate) and math.isnan(r.last_closing_price)


def test_write_rows_to_table_targets_timeseries_hist_dividend_yield(
    fake_db, fixed_today, capsys
):
    rows = [
        pdy.HistDividendYieldRecord.empty_result("yfinance", "a"),
        pdy.HistDividendYieldRecord.empty_result("yfinance", "b"),
    ]

    pdy.write_rows_to_table(fake_db, rows)

    assert fake_db.inserts == [("timeseries", "hist_dividend_yield", rows)]
    assert "count=2, last_row_id=2" in capsys.readouterr().out


# --- get_ycharts_dividend -------------------------------------------------------------------


def test_get_ycharts_dividend_parses_page_name_date_span(monkeypatch):
    seen = {}

    def fake_get(url, headers):
        seen.update(url=url, headers=headers)
        return _Resp(
            '<html><span class="page-name-date">4.56% for Oct. 10 2025</span></html>'
        )

    monkeypatch.setattr(pdy.requests, "get", fake_get)

    r = pdy.get_ycharts_dividend("VZ")

    assert r.rate == pytest.approx(4.56)
    assert r.source == "ycharts"
    assert seen["url"] == "https://ycharts.com/companies/VZ/dividend_yield"
    assert "User-Agent" in seen["headers"]


def test_get_ycharts_dividend_without_span_leaves_rate_nan(monkeypatch):
    monkeypatch.setattr(
        pdy.requests, "get", lambda url, headers: _Resp("<html><p>blocked</p></html>")
    )
    assert math.isnan(pdy.get_ycharts_dividend("VZ").rate)


def test_get_ycharts_dividend_swallows_network_errors(monkeypatch):
    def boom(url, headers):
        raise ConnectionError("down")

    monkeypatch.setattr(pdy.requests, "get", boom)
    r = pdy.get_ycharts_dividend("VZ")
    assert math.isnan(r.rate) and r.symbol == "VZ"


# --- get_yfinance_dividend ------------------------------------------------------------------


def test_get_yfinance_dividend_converts_fraction_to_percent(monkeypatch):
    seen = []
    monkeypatch.setattr(
        pdy.yf,
        "Ticker",
        _ticker_factory({"currentPrice": 40.0, "dividendYield": 0.065}, seen),
    )

    r = pdy.get_yfinance_dividend("vz")

    assert seen == ["VZ"]
    assert r.rate == pytest.approx(6.5)
    assert r.last_closing_price == 40.0
    assert r.source == "yfinance"


def test_get_yfinance_dividend_missing_fields_leaves_nan(monkeypatch):
    monkeypatch.setattr(pdy.yf, "Ticker", _ticker_factory({"currentPrice": 40.0}))
    r = pdy.get_yfinance_dividend("VZ")
    assert r.last_closing_price == 40.0  # set before the KeyError
    assert math.isnan(r.rate)


def test_get_yfinance_dividend_swallows_errors(monkeypatch):
    monkeypatch.setattr(pdy.yf, "Ticker", _ticker_factory(RuntimeError("rate limited")))
    assert math.isnan(pdy.get_yfinance_dividend("VZ").rate)


# --- main -----------------------------------------------------------------------------------


@pytest.fixture
def sources(monkeypatch, fixed_today):
    """Patch both fetchers with symbol-keyed rates; returns a call log {"ycharts": [...], "yfinance": [...]}."""
    calls = {"ycharts": [], "yfinance": []}
    rates = {"AAA": 3.0, "BBB": 7.5, "CCC": 0.0, "DDD": float("nan")}

    def yc(s):
        calls["ycharts"].append(s)
        r = pdy.HistDividendYieldRecord.empty_result("ycharts", s)
        r.rate = rates.get(s.upper(), 1.0) + 0.1
        return r

    def yf_(s):
        calls["yfinance"].append(s)
        r = pdy.HistDividendYieldRecord.empty_result("yfinance", s)
        r.rate = rates.get(s.upper(), 1.0)
        r.last_closing_price = 100.0
        return r

    monkeypatch.setattr(pdy, "get_ycharts_dividend", yc)
    monkeypatch.setattr(pdy, "get_yfinance_dividend", yf_)
    return calls


def test_main_single_symbol_prints_both_sources(
    sources, fake_db, symbols, argv, capsys
):
    symbols(["aaa"])
    argv("aaa")

    pdy.main()

    out = capsys.readouterr().out
    assert sources == {"ycharts": ["AAA"], "yfinance": ["AAA"]}
    assert "ycharts: 3.1" in out
    assert "yfinance: 3.0" in out
    assert fake_db.connected is False


def test_main_multi_symbol_skips_ycharts_by_default_and_tabulates_positive_yields(
    sources, fake_db, symbols, argv, capsys
):
    symbols(["AAA", "BBB", "CCC", "DDD"])
    argv("my_sorted_symbols.txt")

    pdy.main()

    out = capsys.readouterr().out
    assert sources["ycharts"] == []
    assert sources["yfinance"] == ["AAA", "BBB", "CCC", "DDD"]
    assert "Total symbol count: 4" in out
    rows = [line.split() for line in out.splitlines() if line.startswith("yfinance:")]
    assert [(k, float(v)) for k, v in rows] == [
        ("yfinance:BBB", 7.5),
        ("yfinance:AAA", 3.0),
    ]  # sorted descending
    assert "yfinance:CCC" not in out  # zero yield excluded
    assert "yfinance:DDD" not in out  # nan yield excluded
    assert fake_db.connected is False


def test_main_multi_symbol_can_enable_ycharts_and_copies_price_from_yfinance(
    sources, fake_db, symbols, argv, capsys
):
    symbols(["AAA", "BBB"])
    argv("my_sorted_symbols.txt", "--skip-ycharts=false")

    pdy.main()

    out = capsys.readouterr().out
    assert sources["ycharts"] == ["AAA", "BBB"]
    assert "ycharts:AAA" in out and "ycharts:BBB" in out
    # the ycharts record is printed with the yfinance closing price copied onto it
    assert (
        "source='ycharts', symbol='AAA'" in out
        and "last_closing_price=100.0, rate=3.1" in out
    )


def test_main_watchlist_keyword_expands_to_module_watchlist(
    sources, fake_db, symbols, argv
):
    symbols(["watchlist"])
    argv("watchlist")

    pdy.main()

    assert sources["yfinance"] == pdy.watchlist
    assert len(pdy.watchlist) > 1


def test_main_dry_run_false_connects_and_writes_positive_yields_only(
    sources, fake_db, symbols, argv, monkeypatch
):
    monkeypatch.setattr(
        pdy.random, "randint", lambda a, b: 10**9
    )  # disable mid-run flush
    symbols(["AAA", "BBB", "CCC", "DDD"])
    argv("my_sorted_symbols.txt", "--skip-ycharts=true", "--dry-run=false")

    pdy.main()

    assert fake_db.connected is True
    assert [(r.source, r.symbol, r.rate) for r in fake_db.rows] == [
        ("yfinance", "AAA", 3.0),
        ("yfinance", "BBB", 7.5),
    ]
    assert len(fake_db.inserts) == 1


def test_main_flushes_buffer_periodically_once_more_than_ten_rows(
    sources, fake_db, symbols, argv, monkeypatch, capsys
):
    monkeypatch.setattr(pdy.random, "randint", lambda a, b: 3)
    syms = [f"S{i:02d}" for i in range(15)]  # all have rate 1.0 via the fixture default
    symbols(syms)
    argv("my_sorted_symbols.txt", "--skip-ycharts=true", "--dry-run=false")

    pdy.main()

    # buffer exceeds 10 after symbol index 10; first index after that divisible by 3 is 12
    assert [len(rows) for _, _, rows in fake_db.inserts] == [12, 3]
    assert [r.symbol for r in fake_db.rows] == syms
    assert "Progress: 12 of 15" in capsys.readouterr().out
