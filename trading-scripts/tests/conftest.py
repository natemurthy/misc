"""Shared fixtures for the trading-scripts unit tests.

Every script under test is a thin CLI around a few pure functions plus calls out to the
network (yfinance, TipRanks, ycharts, Gemini, Playwright) and Postgres. The fixtures here
replace those edges so each test runs offline, deterministically, and in a temp directory.
"""

import datetime as dt
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _stub_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


def _install_optional_stubs() -> None:
    """pull_fcf_data imports google.generativeai and playwright at module level. Both are
    heavy optional dependencies (API client, browser binaries). Stub them only when they are
    not installed so the module is importable; tests patch the specific attributes they use.
    """
    try:
        import google.generativeai  # noqa: F401
    except ImportError:
        try:
            import google  # may exist as a namespace package (e.g. via protobuf)
        except ImportError:
            google = _stub_module("google")
        genai = _stub_module(
            "google.generativeai",
            configure=lambda **kw: None,
            upload_file=lambda *a, **kw: None,
            GenerativeModel=object,
        )
        google.generativeai = genai
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        sync_api = _stub_module("playwright.sync_api", sync_playwright=lambda: None)
        pw = sys.modules.get("playwright") or _stub_module("playwright")
        pw.sync_api = sync_api


_install_optional_stubs()


FIXED_TODAY = dt.date(2025, 5, 8)


@pytest.fixture
def fixed_today(monkeypatch):
    """Pin util.today_us_pacific() so trading_day / release_date fields are deterministic."""
    import util

    monkeypatch.setattr(util, "today_us_pacific", lambda: FIXED_TODAY)
    return FIXED_TODAY


class FakeDbClient:
    """Stand-in for db.PostgresClient that records connect() and insert() calls."""

    def __init__(self):
        self.connected = False
        self.inserts: list[tuple[str, str, list]] = []

    def connect(self):
        self.connected = True
        return self

    def insert(self, schema_name, table_name, rows, id_column="id"):
        rows = list(rows)  # callers .clear() their buffer after insert, so snapshot it
        self.inserts.append((schema_name, table_name, rows))
        return list(range(1, len(rows) + 1))

    @property
    def rows(self) -> list:
        return [r for _, _, rows in self.inserts for r in rows]


@pytest.fixture
def fake_db(monkeypatch):
    """Replace db.market_data_db_client() with a recording fake."""
    import db

    client = FakeDbClient()
    monkeypatch.setattr(db, "market_data_db_client", lambda: client)
    return client


@pytest.fixture
def symbols(monkeypatch):
    """Patch util.get_symbols so main() never reads my_sorted_symbols.txt or index lists.

    Usage: symbols(["AAPL", "MSFT"])
    """
    import util

    def _set(syms):
        syms = list(syms)
        monkeypatch.setattr(util, "get_symbols", lambda arg: list(syms))
        return syms

    return _set


@pytest.fixture
def argv(monkeypatch):
    """Set sys.argv for scripts that parse it directly. Usage: argv("AAPL", "--dry-run=false")"""

    def _set(*args):
        monkeypatch.setattr(sys, "argv", ["prog", *args])

    return _set


@pytest.fixture
def no_sleep(monkeypatch):
    """Turn time.sleep into a recorder so rate-limit back-offs don't slow the suite."""
    import time

    calls: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: calls.append(s))
    return calls


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    """chdir into a fresh temp dir; scripts read/write relative paths in cwd."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
