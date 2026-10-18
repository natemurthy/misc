import pytest

import cleanup_portfolio_downloads as cpd

# Shape of a raw E*Trade "PortfolioDownload-*.csv": 10 preamble lines, a header row, position
# rows, then 6 trailer lines (CASH, TOTAL, three blanks, "Generated at ...").
ETRADE_PREAMBLE = [
    "Account Summary",
    "Account,Net Account Value,Total Gain $,Total Gain %,Day's Gain Unrealized $,Day's Gain Unrealized %,Available For Withdrawal,Cash Purchasing Power",
    '"Individual Brokerage -1234",64179.92,25357.82,58.68,19.25,.03,5077.11,5077.11',
    "",
    "",
    "View Summary - All Positions",
    "Filters applied: ",
    "Symbol,Security type(s),Sort by,Sort order,",
    ",All,Total Gain %,Asc,",
    "",
]
ETRADE_COLUMNS = "Symbol,Last Price $,Change $,Change %,Quantity,Price Paid $,Day's Gain $,Total Gain $,Total Gain %,Value $"
ETRADE_ROWS = [
    "TSLA,276.22,0.87,0.32,101.0000,60.7314,87.8700,21764.3500,354.8225,27898.2200",
    "CORZ,8.90,-0.09,-1.00,465.0000,0.8721,-41.8500,3725.8102,902.8114,4138.5000",
]
ETRADE_FOOTER = [
    "CASH,,,,,,,,,5224.45,",
    "TOTAL,,,,,33597.64,19.25,25357.82,58.68,64179.92,",
    "",
    "",
    "",
    "Generated at May 8 2025 12:22 AM ET...",
]
ETRADE_TOTAL = 27898.22 + 4138.50

# Shape of a raw Fidelity "Portfolio_Positions_*.csv": header row, position rows, then 6
# trailer lines (blank, disclaimer, blank, disclaimer, blank, "Date downloaded ...").
FIDELITY_COLUMNS = (
    "Account Number,Account Name,Symbol,Description,Quantity,Last Price,Last Price Change,"
    "Current Value,Today's Gain/Loss Dollar,Today's Gain/Loss Percent,Total Gain/Loss Dollar,"
    "Total Gain/Loss Percent,Percent Of Account,Cost Basis Total,Average Cost Basis,Type"
)
FIDELITY_ROWS = [
    "172700185,ROTH IRA,NVDA,NVIDIA CORPORATION COM,174.75,$117.06,+$3.52,$20456.23,+$615.12,+3.10%,+$17627.81,+623.23%,30.44%,$2828.42,$16.19,Cash",
    "172700185,ROTH IRA,QQQ,INVESCO QQQ TR UNIT SER 1,12.15,$483.30,+$1.89,$5872.09,+$22.96,+0.39%,+$2575.80,+78.14%,8.74%,$3296.29,$271.30,Cash",
    "172700185,ROTH IRA,Pending Activity,,,,,--,,,,,,,,",
]
FIDELITY_FOOTER = [
    "",
    '"The data and information in this spreadsheet is provided to you solely for your use."',
    "",
    '"Brokerage services are provided by Fidelity Brokerage Services LLC (FBS)."',
    "",
    '"Date downloaded May-08-2025 12:25 a.m ET"',
]
FIDELITY_TOTAL = 20456.23 + 5872.09


def _write(path, lines):
    path.write_text("\n".join(lines) + "\n")


def _nonblank_lines(path):
    return [line for line in path.read_text().splitlines() if line.strip()]


def make_etrade(workdir, name="PortfolioDownload-1234.csv", rows=ETRADE_ROWS):
    _write(
        workdir / name, ETRADE_PREAMBLE + [ETRADE_COLUMNS] + list(rows) + ETRADE_FOOTER
    )
    return name


def make_fidelity(
    workdir, name="Portfolio_Positions_May-08-2025.csv", rows=FIDELITY_ROWS
):
    _write(workdir / name, [FIDELITY_COLUMNS] + list(rows) + FIDELITY_FOOTER)
    return name


# --- cleanup_portfolio_csv ------------------------------------------------------------------


def test_cleanup_etrade_strips_preamble_and_trailer(workdir):
    name = make_etrade(workdir)

    out = cpd.cleanup_portfolio_csv(name)

    assert out == f"clean-{name}"
    assert _nonblank_lines(workdir / out) == [ETRADE_COLUMNS] + ETRADE_ROWS


def test_cleanup_fidelity_strips_trailer(workdir):
    name = make_fidelity(workdir)

    out = cpd.cleanup_portfolio_csv(name)

    assert out == f"clean-{name}"
    assert _nonblank_lines(workdir / out) == [FIDELITY_COLUMNS] + FIDELITY_ROWS


def test_cleanup_unknown_broker_writes_empty_file(workdir):
    (workdir / "Portfolio-other.csv").write_text("a,b\n1,2\n")

    out = cpd.cleanup_portfolio_csv("Portfolio-other.csv")

    assert (workdir / out).read_text() == ""


def test_cleanup_echoes_last_line_of_source(workdir, capsys):
    name = make_etrade(workdir)
    cpd.cleanup_portfolio_csv(name)
    assert f"{name} Generated at May 8 2025 12:22 AM ET..." in capsys.readouterr().out


# --- _from_fidelity_value_to_float ----------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("$20456.23", 20456.23),
        ("-$5.50", -5.5),
        ("0.5", 0.5),
        ("nan", 0.0),
        ("--", 0.0),
    ],
)
def test_from_fidelity_value_to_float(raw, expected):
    assert cpd._from_fidelity_value_to_float(raw) == pytest.approx(expected)


def test_from_fidelity_value_to_float_rejects_garbage():
    with pytest.raises(ValueError):
        cpd._from_fidelity_value_to_float("abc")


# --- get_total_value ------------------------------------------------------------------------


def test_get_total_value_etrade_sums_value_column(workdir):
    clean = cpd.cleanup_portfolio_csv(make_etrade(workdir))
    assert cpd.get_total_value(clean) == pytest.approx(ETRADE_TOTAL)


def test_get_total_value_fidelity_parses_dollar_strings_and_skips_dashes(workdir):
    clean = cpd.cleanup_portfolio_csv(make_fidelity(workdir))
    assert cpd.get_total_value(clean) == pytest.approx(FIDELITY_TOTAL)


def test_get_total_value_unknown_broker_is_zero(workdir):
    (workdir / "clean-other.csv").write_text("Symbol,Value $\nX,1.0\n")
    assert cpd.get_total_value("clean-other.csv") == 0.0


# --- main -----------------------------------------------------------------------------------


def test_main_cleans_every_portfolio_file_and_prints_grand_total(workdir, capsys):
    et = make_etrade(workdir)
    fi = make_fidelity(workdir)
    (workdir / "clean-PortfolioDownload-old.csv").write_text(
        "stale\n"
    )  # must be ignored
    (workdir / "PortfolioDir").mkdir()  # directories must be ignored
    (workdir / "notes.txt").write_text("ignored\n")

    cpd.main()

    out = capsys.readouterr().out
    assert (workdir / f"clean-{et}").exists()
    assert (workdir / f"clean-{fi}").exists()
    assert (workdir / "clean-clean-PortfolioDownload-old.csv").exists() is False
    assert f"Total Value ${ETRADE_TOTAL + FIDELITY_TOTAL:,.2f}" in out


def test_main_with_no_portfolio_files_reports_zero(workdir, capsys):
    cpd.main()
    assert "Total Value $0.00" in capsys.readouterr().out
