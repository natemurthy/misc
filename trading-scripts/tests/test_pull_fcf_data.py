import datetime as dt
import sys

import pytest

import const
import pull_fcf_data as pf


# --- HistFreeCashFlow -----------------------------------------------------------------------


def test_empty_result_is_a_sentinel_row(fixed_today):
    r = pf.HistFreeCashFlow.empty_result("jd")

    assert r.id is None
    assert r.created_at is None
    assert r.symbol == "JD"
    assert r.release_date == fixed_today
    assert r.ycharts_raw_fcf == "-infinity"
    assert r.fcf_usd == -sys.maxsize - 1


def test_write_rows_to_table_targets_timeseries_hist_free_cash_flow(
    fake_db, fixed_today, capsys
):
    rows = [pf.HistFreeCashFlow.empty_result("jd")]

    pf.write_rows_to_table(fake_db, rows)

    assert fake_db.inserts == [("timeseries", "hist_free_cash_flow", rows)]
    assert "info_write_rows_to_table: [1]" in capsys.readouterr().out


# --- str_to_usd -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2M", 2_000_000),
        ("0.5M", 500_000),
        ("1.2345M", 1_234_500),
        ("1.25B", 1_250_000_000),
        ("-3.2B", -3_200_000_000),
        ("-0.75M", -750_000),
        ("42", 0),  # no magnitude suffix -> unparsed
        ("", 0),
    ],
)
def test_str_to_usd(raw, expected):
    assert pf.str_to_usd(raw) == expected
    assert isinstance(pf.str_to_usd(raw), int)


@pytest.mark.xfail(
    strict=True, reason="'K' suffix is scaled by 1e6 instead of 1e3 in str_to_usd"
)
def test_str_to_usd_thousands_suffix():
    assert pf.str_to_usd("1.5K") == 1_500


def test_str_to_usd_rejects_non_numeric_mantissa():
    with pytest.raises(ValueError):
        pf.str_to_usd("abcM")


# --- str_to_date ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2023-12-31", dt.date(2023, 12, 31)),
        ("2024-02-29", dt.date(2024, 2, 29)),  # real leap day parses as-is
        ("2023-04-31", dt.date(2023, 4, 30)),  # LLM hallucinated 31st -> clamp to 30th
        ("2018-02-29", dt.date(2018, 2, 28)),  # non-leap 29th -> clamp to 28th
    ],
)
def test_str_to_date(raw, expected):
    assert pf.str_to_date(raw) == expected


@pytest.mark.parametrize("raw", ["2023-02-30", "not-a-date", "", "12/31/2023"])
def test_str_to_date_returns_none_when_unfixable(raw):
    assert pf.str_to_date(raw) is None


def test_str_to_date_feb_31_falls_through_to_invalid_feb_30():
    # Only one clamp is attempted, so Feb 31 -> Feb 30 still fails to parse.
    with pytest.raises(ValueError):
        pf.str_to_date("2023-02-31")


# --- capture_fcf_screenshot -----------------------------------------------------------------


class _FakePlaywright:
    """Records the chromium -> page -> goto/screenshot/close sequence."""

    def __init__(self):
        self.events = []

    # context manager returned by sync_playwright()
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.events.append("exit")
        return False

    @property
    def chromium(self):
        return self

    def launch(self):
        self.events.append("launch")
        return self

    def new_page(self):
        self.events.append("new_page")
        return self

    def goto(self, url):
        self.events.append(("goto", url))

    def screenshot(self, path, full_page):
        self.events.append(("screenshot", path, full_page))

    def close(self):
        self.events.append("close")


def test_capture_fcf_screenshot_visits_ycharts_and_saves_png(monkeypatch, capsys):
    fake = _FakePlaywright()
    monkeypatch.setattr(pf, "sync_playwright", lambda: fake)

    out = pf.capture_fcf_screenshot("jd")

    assert out == "fcf_screenshot_jd.png"
    assert fake.events == [
        "launch",
        "new_page",
        ("goto", "https://ycharts.com/companies/JD/free_cash_flow"),
        ("screenshot", "fcf_screenshot_jd.png", True),
        "close",
        "exit",
    ]
    assert "https://ycharts.com/companies/JD/free_cash_flow" in capsys.readouterr().out


# --- extract_fcf_table_data -----------------------------------------------------------------


def _patch_genai(monkeypatch, text="Date,Value\n2023-12-31,1.5B\n"):
    calls = {}

    class FakeModel:
        def __init__(self, name):
            calls["model"] = name

        def generate_content(self, parts):
            calls["parts"] = parts
            return type("R", (), {"text": text})()

    monkeypatch.setattr(
        pf.genai, "configure", lambda **kw: calls.update(configure=kw), raising=False
    )
    monkeypatch.setattr(
        pf.genai,
        "upload_file",
        lambda f: calls.update(uploaded=f) or "<file-handle>",
        raising=False,
    )
    monkeypatch.setattr(pf.genai, "GenerativeModel", FakeModel, raising=False)
    return calls


def test_extract_fcf_table_data_uploads_screenshot_and_prompts_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    calls = _patch_genai(monkeypatch)

    text = pf.extract_fcf_table_data("shot.png")

    assert text == "Date,Value\n2023-12-31,1.5B\n"
    assert calls["configure"] == {"api_key": "test-key"}
    assert calls["uploaded"] == "shot.png"
    assert calls["model"] == "gemini-1.5-flash"
    assert calls["parts"] == ["<file-handle>", "\n\n", pf.prompt]


def test_extract_fcf_table_data_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    _patch_genai(monkeypatch)

    with pytest.raises(KeyError):
        pf.extract_fcf_table_data("shot.png")


# --- main -----------------------------------------------------------------------------------


@pytest.fixture
def scraper(monkeypatch):
    """Replace the screenshot + LLM steps; returns the list of symbols actually scraped."""
    scraped = []
    monkeypatch.setattr(
        pf, "capture_fcf_screenshot", lambda s: scraped.append(s) or f"shot_{s}.png"
    )
    monkeypatch.setattr(
        pf,
        "extract_fcf_table_data",
        lambda png: "\n".join(
            [
                "Date,Value",
                "2023-12-31,1.5B",
                "2023-04-31,2M",  # bad date the clamp fixes
                "garbage line without a comma",  # skipped: not 2 fields
                "2022-12-31,abcM",  # skipped: ValueError from str_to_usd
            ]
        ),
    )
    return scraped


def test_main_single_symbol_prints_raw_llm_lines(
    scraper, fake_db, symbols, argv, capsys
):
    symbols(["jd"])
    argv("jd")

    pf.main()

    out = capsys.readouterr().out
    assert scraper == ["jd"]
    assert "Date,Value" in out and "2023-12-31,1.5B" in out
    assert fake_db.connected is False


def test_main_single_etf_symbol_is_skipped(scraper, fake_db, symbols, argv):
    assert "SPY" in const.ETF_SYMBOLS
    symbols(["SPY"])
    argv("SPY")

    pf.main()

    assert scraper == []


def test_main_multi_symbol_dry_run_parses_rows_and_prints_them(
    scraper, fake_db, fixed_today, symbols, argv, capsys
):
    symbols(["AAA", "SPY", "BBB"])
    argv("my_sorted_symbols.txt")

    pf.main()

    out = capsys.readouterr().out
    assert scraper == ["AAA", "BBB"]  # ETF skipped
    assert out.count("2023-12-31 1.5B 1500000000") == 2
    assert out.count("2023-04-30 2M 2000000") == 2
    assert "skipping=" in out  # the abcM row is reported, not fatal
    assert fake_db.connected is False
    assert fake_db.inserts == []


def test_main_multi_symbol_writes_one_batch_per_symbol(
    scraper, fake_db, fixed_today, symbols, argv
):
    symbols(["AAA", "SPY", "BBB"])
    argv("my_sorted_symbols.txt", "--dry-run=false")

    pf.main()

    assert fake_db.connected is True
    assert [t[:2] for t in fake_db.inserts] == [
        ("timeseries", "hist_free_cash_flow")
    ] * 2
    rows = fake_db.rows
    assert [r.symbol for r in rows] == ["AAA", "AAA", "BBB", "BBB"]
    assert {(r.release_date, r.ycharts_raw_fcf, r.fcf_usd) for r in rows} == {
        (dt.date(2023, 12, 31), "1.5B", 1_500_000_000),
        (dt.date(2023, 4, 30), "2M", 2_000_000),
    }


def test_main_multi_symbol_respects_cloud_run_worker_slice(
    scraper, fake_db, symbols, argv, monkeypatch
):
    symbols(["AAA", "BBB", "CCC"])
    argv("my_sorted_symbols.txt")
    monkeypatch.setenv("CLOUD_RUN_TASK_COUNT", "2")
    monkeypatch.setenv("CLOUD_RUN_TASK_INDEX", "1")

    pf.main()

    assert scraper == ["CCC"]  # worker 0 gets [AAA, BBB], worker 1 gets [CCC]
