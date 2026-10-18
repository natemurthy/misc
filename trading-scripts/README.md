# trading-scripts

These are some helpful scripts that pull data to inform trade decisions on various financial instruments (mostly
stocks, ETFs, and options) in anyone's brokerage portfolio. Consider the following portfolio CSV dumps:

```
Portfolio_Positions_Sep-21-2024.csv  // fidelity
PortfolioDownload-0431.csv           // etrade
PortfolioDownload-3327.csv
PortfolioDownload-6491.csv
PortfolioDownload-6750.csv
```

## Usage

First cleanup the portfolio download files so that header and footer rows have been removed with

```bash
python cleanup_portfolio_downloads.py
```

Then extract every unique ticker symbol and save to `my_sorted_symbols.txt`

```bash
python extract_symbols.py
```

This output file may be used as input to any of the pull scripts


## Testing

Unit tests live in `tests/`, one file per script that has a `main()`. They run fully offline:
network calls (yfinance, TipRanks, ycharts, Gemini, Playwright) and Postgres are replaced with
fakes from `tests/conftest.py`, and file-based scripts run inside a temp directory.

```bash
pip install pytest
python -m pytest
```

Two tests are marked `xfail(strict=True)` to pin known bugs (`str_to_usd` scales a `K` suffix by
1e6, and `fetch_tipranks_estimates` crashes on a network error). They start failing, and so flag
themselves, once the underlying bug is fixed.

## TODO

More notes TBD when this code stabilizes
