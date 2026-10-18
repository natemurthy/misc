import db
import upload_symbols as us


def test_holdings_is_a_simple_symbol_record():
    h = us.Holdings("AAPL")
    assert h.symbol == "AAPL"
    assert h == us.Holdings("AAPL")
    assert h != us.Holdings("MSFT")


def test_holdings_exposes_only_symbol_as_insertable_column():
    # The real client derives INSERT columns from the dataclass fields; Holdings must map to
    # exactly the single "symbol" column in portfolio.holdings.
    assert db.PostgresClient._get_insertable_columns(us.Holdings("AAPL")) == ["symbol"]


def test_write_rows_to_table_targets_portfolio_holdings(fake_db, capsys):
    rows = [us.Holdings("AAPL"), us.Holdings("MSFT")]

    us.write_rows_to_table(fake_db, rows)

    assert fake_db.inserts == [("portfolio", "holdings", rows)]
    assert "Rows written to database: [1, 2]" in capsys.readouterr().out


def test_main_dry_run_by_default_never_connects_or_writes(
    fake_db, symbols, argv, capsys
):
    symbols(["AAPL", "MSFT", "NVDA"])
    argv("my_sorted_symbols.txt")

    us.main()

    assert fake_db.connected is False
    assert fake_db.inserts == []
    out = capsys.readouterr().out
    assert "Uploading 'my_sorted_symbols.txt'" in out
    assert "Total symbol count: 3" in out


def test_main_explicit_dry_run_true_does_not_write(fake_db, symbols, argv):
    symbols(["AAPL"])
    argv("AAPL", "--dry-run=true")

    us.main()

    assert fake_db.connected is False
    assert fake_db.inserts == []


def test_main_dry_run_false_connects_and_uploads_every_symbol(fake_db, symbols, argv):
    symbols(["AAPL", "MSFT"])
    argv("my_sorted_symbols.txt", "--dry-run=false")

    us.main()

    assert fake_db.connected is True
    assert fake_db.rows == [us.Holdings("AAPL"), us.Holdings("MSFT")]
    assert [t[:2] for t in fake_db.inserts] == [("portfolio", "holdings")]


def test_main_dry_run_false_with_no_symbols_skips_insert(fake_db, symbols, argv):
    symbols([])
    argv("my_sorted_symbols.txt", "--dry-run=false")

    us.main()

    assert fake_db.connected is True
    assert fake_db.inserts == []
