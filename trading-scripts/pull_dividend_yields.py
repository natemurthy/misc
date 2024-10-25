import db
import  math
import util
import random
import requests
import sys
import yfinance as yf

from bs4 import BeautifulSoup
from dataclasses import dataclass
from tabulate import tabulate


watchlist = [
    "AGG",
    "AGGH",
    "BEP",
    "BITO",
    "BUCK",
    "CDX",
    "CMA",
    "CTA",
    "EQLS",
    "F",
    "FLOT",
    "GSL",
    "HIGH",
    "ILF",
    "KEY",
    "MUB",
    "O",
    "PFF",
    "STLA",
    "SVOL",
    "T",
    "VOD",
    "VZ",
]


@dataclass
class HistDividendYieldRecord(db.TableRowStruct):
    rate: float # between 0 and 100% (i.e. basis points)

    @staticmethod
    def empty_result(source: db.SourceLiteral, s: str):
        nan = float("nan")
        return HistDividendYieldRecord(
            id=None,
            created_at=None,
            source=source,
            symbol=s.upper(),
            trading_day=util.today_us_pacific(),
            last_closing_price=nan,
            rate=nan,
        )


def write_rows_to_table(c: db.PostgresClient, data: list[HistDividendYieldRecord]) -> None:
    ids_written = c.insert(
        schema_name="timeseries",
        table_name="hist_dividend_yield",
        rows=data,
    )
    print(f"Rows written to database: count={len(ids_written)}, last_row_id={ids_written[-1]}")


def get_ycharts_dividend(s: str) -> HistDividendYieldRecord:
    url = f"https://ycharts.com/companies/{s}/dividend_yield"
    r = HistDividendYieldRecord.empty_result("ycharts", s)
    try:
        resp = requests.get(url, headers=util.get_random_user_agent_header())
        html_text = resp.text
        soup = BeautifulSoup(html_text, 'html.parser')
        span= soup.find_all("span", {"class": "page-name-date"})
        if len(span) > 0:
            dividend_yield = float(span[0].contents[0].split("% for")[0])
            r.rate = dividend_yield
            #print(r)
        else:
            #print(span)
            pass
    except Exception as ex:
        #print(url, ex)
        pass
    return r


def get_yfinance_dividend(s: str) -> HistDividendYieldRecord:
    r = HistDividendYieldRecord.empty_result("yfinance", s)
    try:
        info = yf.Ticker(s.upper()).info
        r.last_closing_price = info["currentPrice"]
        r.rate = info["dividendYield"] * 100
    except Exception as ex:
        #print("yfinance", s, ex)
        pass
    return r

def main():
    print(f"Fetching dividend yield numbers from for '{sys.argv[1]}'")
    symbols = util.get_symbols(sys.argv[1])
    skip_ycharts = True
    write_to_db = False
    if len(sys.argv) > 2:
        skip_ycharts = sys.argv[2] != "--skip-ycharts=false"
    if len(sys.argv) > 3:
        write_to_db = sys.argv[3] == "--dry-run=false"

    db_client = db.market_data_db_client()

    if write_to_db:
        db_client.connect()
    
    if symbols[0] == "watchlist":
        symbols = watchlist

    k = len(symbols)
    print(f"Total symbol count: {k}")

    results_stdout = {}
    results_dbwrite: list[HistDividendYieldRecord] = []

    if k > 1:
        for i, s in  enumerate(symbols):
            yc_r = HistDividendYieldRecord.empty_result("ycharts", s)
            yf_r = get_yfinance_dividend(s)

            if len(results_dbwrite) > 10 and i % random.randint(3,8) == 0:
                write_rows_to_table(db_client, results_dbwrite)
                print(f"Progress: {i} of {k}")
                results_dbwrite.clear()

            if not skip_ycharts:
                yc_r = get_ycharts_dividend(s)
                # we already have the closing price from yfinance, so set it on the ycharts result
                yc_r.last_closing_price = yf_r.last_closing_price

            if not skip_ycharts and not math.isnan(yc_r.rate) and yc_r.rate > 0:
                if not write_to_db:
                    results_stdout[f"ycharts:{s}"] = yc_r.rate
                    print(yc_r)
                else:
                    results_dbwrite.append(yc_r)
            if not math.isnan(yf_r.rate) and yf_r.rate > 0:
                if not write_to_db:
                    results_stdout[f"yfinance:{s}"] = yf_r.rate
                    print(yf_r)
                else:
                    results_dbwrite.append(yf_r)

        if write_to_db and len(results_dbwrite) > 0:
            # if there is anything else left in the buffer, flush to the database
            write_rows_to_table(db_client, results_dbwrite)
        else:
            sorted_results = sorted(results_stdout.items(), key=lambda x:x[1], reverse=True)
            table_header = ["Symbol", "Dividend Yield"]
            row_results = []
            for k, v in sorted_results:
                v_formatted = "{0:.2f}".format(v)
                row_results.append([k, v_formatted])
            print()
            print(tabulate([table_header] + row_results, headers="firstrow"), "\n")
    else:
        s = sys.argv[1].upper()
        print("ycharts:", get_ycharts_dividend(s).rate)
        print("yfinance:", get_yfinance_dividend(s).rate)


if __name__ == "__main__":
    main()
