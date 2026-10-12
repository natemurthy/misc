import pytest

import extract_symbols as es


def _write_clean_csv(path, symbols, header="Symbol,Quantity,Value $"):
    lines = [header] + [f"{s},1,10" for s in symbols]
    path.write_text("\n".join(lines) + "\n")


def test_extract_symbols_keeps_plain_tickers(workdir):
    _write_clean_csv(
        workdir / "clean-PortfolioDownload-1.csv", ["TSLA", "CORZ", "AAPL"]
    )
    assert es.extract_symbols("clean-PortfolioDownload-1.csv") == {
        "TSLA",
        "CORZ",
        "AAPL",
    }


def test_extract_symbols_drops_option_contracts_cusips_and_skip_list(workdir):
    _write_clean_csv(
        workdir / "clean-PortfolioDownload-1.csv",
        [
            "TSLA",
            "QQQ 05/16/2025 470 Put",  # option contract: contains spaces
            "33813J106",  # CUSIP: first char not alphabetic
            "CORE**",  # explicit skip list
            "FSRNQ",  # explicit skip list
            "BRKB",  # explicit skip list
            "Pending Activity",  # Fidelity placeholder: contains a space
        ],
    )
    assert es.extract_symbols("clean-PortfolioDownload-1.csv") == {"TSLA"}


def test_extract_symbols_rewrites_brk_dot_b_to_dash(workdir):
    _write_clean_csv(workdir / "clean-PortfolioDownload-1.csv", ["BRK.B", "MSFT"])
    assert es.extract_symbols("clean-PortfolioDownload-1.csv") == {"BRK-B", "MSFT"}


def test_extract_symbols_dedupes_repeated_positions(workdir):
    _write_clean_csv(
        workdir / "clean-PortfolioDownload-1.csv", ["TSLA", "TSLA", "TSLA"]
    )
    assert es.extract_symbols("clean-PortfolioDownload-1.csv") == {"TSLA"}


def test_extract_symbols_works_on_fidelity_layout(workdir):
    header = "Account Number,Account Name,Symbol,Description,Current Value"
    rows = [
        "1,ROTH IRA,NVDA,NVIDIA,$1",
        "1,ROTH IRA,QQQ,INVESCO,$2",
        "1,ROTH IRA,Pending Activity,,--",
    ]
    (workdir / "clean-Portfolio_Positions_X.csv").write_text(
        "\n".join([header] + rows) + "\n"
    )
    assert es.extract_symbols("clean-Portfolio_Positions_X.csv") == {"NVDA", "QQQ"}


def test_extract_symbols_requires_symbol_column(workdir):
    (workdir / "clean-bad.csv").write_text("Ticker\nTSLA\n")
    with pytest.raises(KeyError):
        es.extract_symbols("clean-bad.csv")


# --- main -----------------------------------------------------------------------------------


def test_main_merges_existing_symbols_with_clean_files_and_rewrites_sorted(
    workdir, capsys
):
    (workdir / "my_sorted_symbols.txt").write_text("ZZZ\nAAPL\n")
    _write_clean_csv(workdir / "clean-PortfolioDownload-1.csv", ["TSLA", "BRK.B"])
    _write_clean_csv(workdir / "clean-Portfolio_Positions_2.csv", ["NVDA", "AAPL"])
    # Raw (not yet cleaned) downloads must be ignored; they still have preamble rows.
    (workdir / "PortfolioDownload-1.csv").write_text("Account Summary\nfoo\n")

    es.main()

    written = (workdir / "my_sorted_symbols.txt").read_text().splitlines()
    assert written == ["AAPL", "BRK-B", "NVDA", "TSLA", "ZZZ"]
    out = capsys.readouterr().out
    assert "Symbol count: 5" in out


def test_main_with_no_clean_files_preserves_existing_symbols(workdir):
    (workdir / "my_sorted_symbols.txt").write_text("B\nA\n")

    es.main()

    assert (workdir / "my_sorted_symbols.txt").read_text() == "A\nB\n"


def test_main_requires_existing_symbol_file(workdir):
    with pytest.raises(FileNotFoundError):
        es.main()
