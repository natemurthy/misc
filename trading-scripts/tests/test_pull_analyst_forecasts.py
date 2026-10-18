import datetime as dt
import math

import pytest
from bs4 import BeautifulSoup

import const
import pull_analyst_forecasts as paf


class _Resp:
    def __init__(self, text):
        self.text = text


def _ticker_factory(info=None, targets=None, seen=None, error=None):
    class T:
        def __init__(self, sym):
            if seen is not None:
                seen.append(sym)
            if error is not None:
                raise error

        @property
        def info(self):
            return info

        @property
        def analyst_price_targets(self):
            return targets

    return T


def tipranks_html(
    high="$200.00",
    mean="$150.00",
    low="$100.00",
    ratings=(3, 2, 1),
    with_potential=True,
):
    spans = "".join(f'<span class="mr2">{n}</span>' for n in ratings)
    potential = (
        '<div class="mt2 displayflex fontSize10">   (+12.34% Upside)</div>'
        if with_potential
        else ""
    )
    cells = "".join(
        f"<td><span>{label}</span><span>{value}</span></td>"
        for label, value in [
            ("High", high),
            ("x", "-"),
            ("Average", mean),
            ("y", "-"),
            ("Low", low),
        ]
    )
    return f"<html>{spans}{potential}<table><tr>{cells}</tr></table></html>"


# --- record -----------------------------------------------------------------------------------


def test_empty_result_forecasts_twelve_months_out(fixed_today):
    r = paf.FcstAnalystPriceTarget.empty_result("tipranks", "nvda")

    assert r.symbol == "NVDA" and r.source == "tipranks"
    assert r.trading_day == fixed_today
    assert r.forecast_date == dt.date(2026, 5, 8)
    assert all(
        math.isnan(getattr(r, f))
        for f in ("last_closing_price", "low", "high", "mean", "upside_potential")
    )
    assert (r.median, r.ratings_count, r.pe_fwd, r.pe_ttm) == (None, None, None, None)


def test_write_rows_to_table_targets_fcst_analyst_price_target(
    fake_db, fixed_today, capsys
):
    rows = [paf.FcstAnalystPriceTarget.empty_result("yfinance", "a")]
    paf.write_rows_to_table(fake_db, rows)
    assert fake_db.inserts == [("timeseries", "fcst_analyst_price_target", rows)]
    assert "count=1, last_row_id=1" in capsys.readouterr().out


# --- html helpers -----------------------------------------------------------------------------


def test_get_ratings_count_sums_buy_hold_sell_spans():
    soup = BeautifulSoup(tipranks_html(ratings=(10, 4, 2)), "html.parser")
    assert (
        paf.get_ratings_count_from_html("x", soup.find_all("span", {"class": "mr2"}))
        == 16
    )


def test_get_ratings_count_returns_zero_and_logs_when_spans_missing(capsys):
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert (
        paf.get_ratings_count_from_html("x", soup.find_all("span", {"class": "mr2"}))
        == 0
    )
    assert "error_get_ratings_count_from_html: symbol=X" in capsys.readouterr().out


def test_get_target_from_html_strips_currency_formatting():
    soup = BeautifulSoup(
        tipranks_html(high="$1,234.50", mean="$999.99", low="$0.10"), "html.parser"
    )
    tr = soup.find_all("tr")
    assert paf.get_target_from_html("x", tr, 0) == 1234.5
    assert paf.get_target_from_html("x", tr, 2) == 999.99
    assert paf.get_target_from_html("x", tr, 4) == 0.1


def test_get_target_from_html_returns_zero_and_logs_on_bad_markup(capsys):
    tr = BeautifulSoup("<table><tr><td>n/a</td></tr></table>", "html.parser").find_all(
        "tr"
    )
    assert paf.get_target_from_html("x", tr, 0) == 0.0
    assert "error_get_target_from_html: symbol=X" in capsys.readouterr().out


# --- fetch_tipranks_estimates -----------------------------------------------------------------


def test_fetch_tipranks_estimates_stock_parses_targets_and_uses_yfinance_price(
    monkeypatch, capsys
):
    seen = {}
    monkeypatch.setattr(
        paf.requests,
        "get",
        lambda url, headers: seen.update(url=url, headers=headers)
        or _Resp(tipranks_html()),
    )
    monkeypatch.setattr(
        paf.yf,
        "Ticker",
        _ticker_factory(info={"quoteType": "EQUITY", "currentPrice": 120.0}),
    )

    r = paf.fetch_tipranks_estimates("nvda")

    assert seen["url"] == "https://www.tipranks.com/stocks/nvda/forecast"
    assert "User-Agent" in seen["headers"]
    assert (r.high, r.mean, r.low) == (200.0, 150.0, 100.0)
    assert r.ratings_count == 6
    assert r.last_closing_price == 120.0
    assert r.upside_potential == pytest.approx(150.0 / 120.0)
    out = capsys.readouterr().out
    assert "TipRanks potential: +12.34% Upside" in out
    assert "TipRanks ratings count: 6" in out


def test_fetch_tipranks_estimates_etf_uses_etf_path_and_mid_price(monkeypatch):
    assert "SPY" in const.ETF_SYMBOLS
    seen = {}
    monkeypatch.setattr(
        paf.requests,
        "get",
        lambda url, headers: seen.update(url=url)
        or _Resp(tipranks_html(with_potential=False)),
    )
    monkeypatch.setattr(
        paf.yf,
        "Ticker",
        _ticker_factory(info={"quoteType": "ETF", "bid": 99.0, "ask": 101.0}),
    )

    r = paf.fetch_tipranks_estimates("spy", print_stdout=False)

    assert seen["url"] == "https://www.tipranks.com/etf/spy/forecast"
    assert r.last_closing_price == 100.0
    assert r.upside_potential == pytest.approx(1.5)


def test_fetch_tipranks_estimates_print_stdout_false_is_quiet(monkeypatch, capsys):
    monkeypatch.setattr(
        paf.requests, "get", lambda url, headers: _Resp(tipranks_html())
    )
    monkeypatch.setattr(
        paf.yf,
        "Ticker",
        _ticker_factory(info={"quoteType": "EQUITY", "currentPrice": 120.0}),
    )

    paf.fetch_tipranks_estimates("nvda", print_stdout=False)

    out = capsys.readouterr().out
    assert "TipRanks potential" not in out and "ratings count" not in out


def test_fetch_tipranks_estimates_html_parse_failure_returns_empty_record(
    monkeypatch, capsys
):
    monkeypatch.setattr(
        paf.requests, "get", lambda url, headers: _Resp("<html>Access denied</html>")
    )

    r = paf.fetch_tipranks_estimates("nvda")

    assert math.isnan(r.mean) and math.isnan(r.upside_potential)
    assert "reason='html parsing error'" in capsys.readouterr().out


def test_fetch_tipranks_estimates_without_price_leaves_upside_nan(monkeypatch, capsys):
    monkeypatch.setattr(
        paf.requests, "get", lambda url, headers: _Resp(tipranks_html())
    )
    monkeypatch.setattr(
        paf.yf, "Ticker", _ticker_factory(error=RuntimeError("rate limited"))
    )

    r = paf.fetch_tipranks_estimates("nvda")

    assert r.mean == 150.0
    assert math.isnan(r.last_closing_price) and math.isnan(r.upside_potential)
    assert "no latest price available from yfinance" in capsys.readouterr().out


def test_fetch_tipranks_estimates_zero_targets_leave_upside_nan(monkeypatch):
    monkeypatch.setattr(
        paf.requests, "get", lambda url, headers: _Resp(tipranks_html(mean="n/a"))
    )
    monkeypatch.setattr(
        paf.yf,
        "Ticker",
        _ticker_factory(info={"quoteType": "EQUITY", "currentPrice": 120.0}),
    )

    r = paf.fetch_tipranks_estimates("nvda", print_stdout=False)

    assert r.mean == 0.0 and math.isnan(r.upside_potential)


@pytest.mark.xfail(
    strict=True,
    raises=UnboundLocalError,
    reason="except-branch logs `r` before requests.get assigned it",
)
def test_fetch_tipranks_estimates_network_error_returns_empty_record(monkeypatch):
    def boom(url, headers):
        raise ConnectionError("down")

    monkeypatch.setattr(paf.requests, "get", boom)

    r = paf.fetch_tipranks_estimates("nvda")

    assert math.isnan(r.mean)


# --- fetch_yfinance_estimates -----------------------------------------------------------------

YF_TARGETS = {
    "current": 100.0,
    "low": 80.0,
    "high": 150.0,
    "mean": 120.0,
    "median": 110.0,
}
YF_INFO = {"trailingPE": 20.5, "forwardPE": 15.25}


def test_fetch_yfinance_estimates_uses_median_for_upside(monkeypatch):
    seen = []
    monkeypatch.setattr(
        paf.yf, "Ticker", _ticker_factory(info=YF_INFO, targets=YF_TARGETS, seen=seen)
    )

    r = paf.fetch_yfinance_estimates("nvda")

    assert seen == ["nvda"] and r.symbol == "NVDA"
    assert (r.last_closing_price, r.low, r.high, r.mean, r.median) == (
        100.0,
        80.0,
        150.0,
        120.0,
        110.0,
    )
    assert r.upside_potential == pytest.approx(1.1)
    assert (r.pe_ttm, r.pe_fwd) == (20.5, 15.25)


def test_fetch_yfinance_estimates_without_median_leaves_upside_nan(monkeypatch):
    monkeypatch.setattr(
        paf.yf,
        "Ticker",
        _ticker_factory(info=YF_INFO, targets={**YF_TARGETS, "median": None}),
    )
    r = paf.fetch_yfinance_estimates("nvda")
    assert r.mean == 120.0 and math.isnan(r.upside_potential)


def test_fetch_yfinance_estimates_swallows_errors(monkeypatch, capsys):
    monkeypatch.setattr(paf.yf, "Ticker", _ticker_factory(error=RuntimeError("boom")))
    r = paf.fetch_yfinance_estimates("nvda")
    assert math.isnan(r.mean) and r.pe_fwd is None
    assert "error_fetch_yfinance_estimates: symbol=NVDA" in capsys.readouterr().out


# --- fetch_analyst_forecasts ------------------------------------------------------------------


@pytest.fixture
def forecast_sources(monkeypatch, fixed_today):
    calls = {"tipranks": [], "yfinance": []}

    def tr(s, print_stdout=True):
        calls["tipranks"].append(s)
        r = paf.FcstAnalystPriceTarget.empty_result("tipranks", s)
        r.mean = 150.0
        return r

    def yf_(s):
        calls["yfinance"].append(s)
        return paf.FcstAnalystPriceTarget.empty_result(
            "yfinance", s
        )  # mean nan -> "no data"

    monkeypatch.setattr(paf, "fetch_tipranks_estimates", tr)
    monkeypatch.setattr(paf, "fetch_yfinance_estimates", yf_)
    return calls


def test_fetch_analyst_forecasts_prints_summary_and_both_sources(
    forecast_sources, monkeypatch, capsys
):
    monkeypatch.setattr(
        paf.yf,
        "Ticker",
        _ticker_factory(info={"shortName": "NVIDIA Corp", "currentPrice": 120.0}),
    )

    paf.fetch_analyst_forecasts("nvda")

    out = capsys.readouterr().out
    assert "Forecasts for NVIDIA Corp (symbol: NVDA, last: $120.0)" in out
    assert forecast_sources == {"tipranks": ["nvda"], "yfinance": ["nvda"]}
    assert "source='tipranks'" in out
    assert "No Yahoo Finance data available" in out


def test_fetch_analyst_forecasts_falls_back_to_ask_for_etfs_and_honours_skips(
    forecast_sources, monkeypatch, capsys
):
    monkeypatch.setattr(
        paf.yf,
        "Ticker",
        _ticker_factory(info={"shortName": "SPDR S&P 500", "ask": 500.5}),
    )

    paf.fetch_analyst_forecasts("spy", skip_tipranks=True, skip_yfinance=True)

    assert "last: $500.5" in capsys.readouterr().out
    assert forecast_sources == {"tipranks": [], "yfinance": []}


# --- main -------------------------------------------------------------------------------------


@pytest.fixture
def main_sources(monkeypatch, fixed_today):
    """Both fetchers return upside = 1 + index/10 for symbols 'S00'..; 'NAN' yields no upside."""
    calls = {"tipranks": [], "yfinance": []}

    def make(source):
        def fetch(s, print_stdout=True):
            calls[source].append(s)
            r = paf.FcstAnalystPriceTarget.empty_result(source, s)
            if s != "NAN":
                r.mean = 100.0
                r.upside_potential = 1 + int(s[1:]) / 10 if s.startswith("S") else 1.5
            return r

        return fetch

    monkeypatch.setattr(paf, "fetch_tipranks_estimates", make("tipranks"))
    monkeypatch.setattr(paf, "fetch_yfinance_estimates", make("yfinance"))
    monkeypatch.setattr(paf.random, "uniform", lambda a, b: 0.0)
    return calls


def test_main_yfinance_source_skips_etfs_sleeps_between_calls_and_tabulates(
    main_sources, no_sleep, fake_db, symbols, argv, capsys
):
    symbols(["S01", "SPY", "S03", "NAN"])
    argv("my_sorted_symbols.txt")

    paf.main()

    out = capsys.readouterr().out
    assert main_sources["yfinance"] == ["S01", "S03", "NAN"]
    assert main_sources["tipranks"] == []
    assert no_sleep == [pytest.approx(0.2)] * 3
    table = out[out.index("Analyst Upside Potential") :]
    rows = [line.split() for line in table.splitlines()[2:] if line.strip()]
    assert [(k, float(v)) for k, v in rows] == [
        ("yfinance:S03", 1.3),
        ("yfinance:S01", 1.1),
    ]
    assert fake_db.connected is False


def test_main_yfinance_source_dry_run_false_writes_rows_with_upside(
    main_sources, no_sleep, fake_db, symbols, argv
):
    symbols(["S01", "S02", "NAN"])
    argv("my_sorted_symbols.txt", "yfinance", "--dry-run=false")

    paf.main()

    assert fake_db.connected is True
    assert [r.symbol for r in fake_db.rows] == ["S01", "S02"]
    assert all(r.source == "yfinance" for r in fake_db.rows)


def test_main_yfinance_source_respects_cloud_run_worker_slice(
    main_sources, no_sleep, fake_db, symbols, argv, monkeypatch
):
    monkeypatch.setenv("CLOUD_RUN_TASK_COUNT", "2")
    monkeypatch.setenv("CLOUD_RUN_TASK_INDEX", "0")
    symbols(["S01", "S02", "S03"])
    argv("my_sorted_symbols.txt")

    paf.main()

    assert main_sources["yfinance"] == ["S01", "S02"]


def test_main_tipranks_source_pauses_every_five_symbols_and_flushes_batches(
    main_sources, no_sleep, fake_db, symbols, argv, capsys
):
    symbols([f"S{i:02d}" for i in range(7)])
    argv("my_sorted_symbols.txt", "tipranks", "--dry-run=false")

    paf.main()

    out = capsys.readouterr().out
    assert main_sources["tipranks"] == [f"S{i:02d}" for i in range(7)]
    assert no_sleep == [pytest.approx(60.5)]  # once, before symbol index 5
    assert "waiting 60.5 sec due to tipranks rate limiter" in out
    assert [len(rows) for _, _, rows in fake_db.inserts] == [5, 2]
    assert all(r.source == "tipranks" for r in fake_db.rows)


def test_main_tipranks_source_dry_run_prints_records_and_table(
    main_sources, no_sleep, fake_db, symbols, argv, capsys
):
    symbols(["S01", "S02"])
    argv("my_sorted_symbols.txt", "tipranks")

    paf.main()

    out = capsys.readouterr().out
    assert out.count("source='tipranks'") == 2
    assert "tipranks:S02" in out
    assert no_sleep == []
    assert fake_db.inserts == []


def test_main_single_symbol_delegates_to_fetch_analyst_forecasts(
    fake_db, symbols, argv, monkeypatch
):
    seen = []
    monkeypatch.setattr(
        paf, "fetch_analyst_forecasts", lambda s, **kw: seen.append((s, kw))
    )

    symbols(["nvda"])
    argv("nvda")
    paf.main()
    symbols(["spy"])
    argv("spy")
    paf.main()

    assert seen == [
        ("nvda", {"skip_yfinance": False}),
        ("spy", {"skip_yfinance": True}),
    ]
