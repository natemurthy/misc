import const
import datetime as dt
import db
import numpy as np
import util
import random
import requests
import sys
import time
import yfinance as yf

from bs4 import BeautifulSoup
from bs4.element import ResultSet
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from tabulate import tabulate


@dataclass
class FcstAnalystPriceTarget(db.TableRowStruct):
    forecast_date: dt.date
    upside_potential: float
    low: float
    high: float
    mean: float
    median: float | None # Yahoo Finance only, not available from TipRanks
    
    @staticmethod
    def empty_result(source: db.SourceLiteral, s: str):
        nan = float("nan")
        return FcstAnalystPriceTarget(
            id=None,
            created_at=None,
            source=source,
            symbol=s.upper(),
            trading_day=util.today_us_pacific(),
            last_closing_price=nan,
            forecast_date=util.today_us_pacific()+relativedelta(months=+12),
            low=nan,
            high=nan,
            mean=nan,
            median=None,
            upside_potential=nan,
        )


class ResultPair:
    def __init__(self):
        self.tipranks: FcstAnalystPriceTarget = FcstAnalystPriceTarget.empty_result("tipranks","")
        self.yfinance: FcstAnalystPriceTarget = FcstAnalystPriceTarget.empty_result("yfinance", "")


def write_rows_to_table(c: db.PostgresClient, data: list[FcstAnalystPriceTarget]) -> None:
    ids_written = c.insert(
        schema_name="timeseries",
        table_name="fcst_analyst_price_target",
        rows=data,
    )
    print(f"Rows written to database: count={len(ids_written)}, last_row_id={ids_written[-1]}")


def get_ratings_count_from_html(span_mr2: ResultSet) -> int:
  try:
    return int(span_mr2[0].contents[0]) + \
        int(span_mr2[1].contents[0]) + \
        int(span_mr2[2].contents[0])
  except:
    return 0


def get_target_from_html(tr: ResultSet, i: int) -> float:
  try:
    return float(tr[0].find_all('td')[i].find_all('span')[1].contents[0].replace("$", "").replace(",", ""))
  except:
    return 0.0


def fetch_tipranks_estimates(s: str, print_stdout: bool = True) -> FcstAnalystPriceTarget:
    """Analyst estimates from TipRanks are available from one of two URL paths dependening on asset type:

        For stocks: https://www.tipranks.com/stocks/{s.lower()}/forecast
        For ETFs:   https://www.tipranks.com/etf/{s.lower()}/forecast

    Where s.lower() is a ticker symbol in lower case. These may be visited with a typical web browser and are often
    restricted / limited to view after a small number of page visits.
    """
    # TODO add rate limiter when called more than 5 times in a row
    k, cur, potential, lo, avg, hi = 0, 0, 0 ,0 ,0, 0
    asset_type = "etf" if s.upper() in const.ETF_SYMBOLS else "stocks"
    url = f"https://www.tipranks.com/{asset_type}/{s.lower()}/forecast"
    res = FcstAnalystPriceTarget.empty_result("tipranks", s.upper())
    try:
        if print_stdout:
            print(f"Scraping {url}")
        r = requests.get(url, headers=const.HEADERS)
    except Exception as ex:
        #print("fetch_tipranks_estimates:", ex)
        return res
    html_text = r.text
    soup = BeautifulSoup(html_text, 'html.parser')
    try:
        span_mr2 = soup.find_all("span", {"class": "mr2"})
        if asset_type == "stocks":
            potential = soup.find_all("div", {"class": "mt2 displayflex fontSize10"})[0].contents[0][3:]
            if print_stdout:
                print("TipRanks potential:", potential.replace("(", "").replace(")", ""))
        tr = soup.find_all('tr')
        k = get_ratings_count_from_html(span_mr2)

        if asset_type == "etf":
            cur = float(soup.find_all("span", {"class": "fontWeightsemibold colorblack"})[21].contents[0].replace("$", "").replace(",", ""))
        if asset_type == "stocks":
            cur = float(soup.find_all("span", {"class": "fontWeightsemibold colorblack"})[22].contents[0].replace("$", "").replace(",", ""))
        hi = get_target_from_html(tr, 0)
        avg = get_target_from_html(tr, 2)
        lo = get_target_from_html(tr, 4)
    except Exception as ex:
        #print("fetch_tipranks_estimates:",  ex)
        return res
    if print_stdout:
        print("TipRanks ratings count:", k)
    res.last_closing_price = cur
    res.low = lo
    res.high = hi
    res.mean = avg
    return res


def fetch_yfinance_estimates(s: str) -> FcstAnalystPriceTarget:
    """Analyst estimates from Yahoo Finance are available from the following URL:

        https://finance.yahoo.com/quote/{s.upper()}/analysis/

    Where s.upper() is the asset ticker symbol in upper case. This web site also provides earnings, revenue, and
    growth estimates alongisde historical earnings, EPS revisions, and EPS trends with analyst recommendations.
    """
    res = FcstAnalystPriceTarget.empty_result("yfinance", s.upper())
    try:
        ticker_data = yf.Ticker(s)
        t = ticker_data.analyst_price_targets
        res.last_closing_price = t["current"]
        res.low = t["low"]
        res.high = t["high"]
        res.mean = t["mean"]
        res.median = t["median"]
    except Exception as ex:
        #print(ex)
        pass
    return res


def fetch_analyst_forecasts(s: str, skip_tipranks: bool = False, skip_yfinance: bool = False):
    ticker_data = yf.Ticker(s)
    short_name: str = ticker_data.info["shortName"] 
    try:
        curr_price = ticker_data.info["currentPrice"]
    except KeyError:
        curr_price = ticker_data.info["previousClose"]
    summary: str = f"Forecasts for {short_name} (symbol: {s.upper()}, last: ${curr_price})"
    print(summary)

    if not skip_tipranks:
        r = fetch_tipranks_estimates(s)
        if not np.isnan(r.mean):
            print(r)
        else:
            print("No TipRanks data available")

    if not skip_yfinance:
        r = fetch_yfinance_estimates(s)
        if not np.isnan(r.mean):
            print(r)
        else:
            print("No Yahoo Finance data available")


def main():
    print(f"Fetching analyst price targets/estimates for '{sys.argv[1]}' (12-month forecast)")
    symbols = util.get_symbols(sys.argv[1])
    skip_tipranks = True
    write_to_db = False
    if len(sys.argv) > 2:
        skip_tipranks = sys.argv[2] != "--skip-tipranks=false"
    if len(sys.argv) > 3:
        write_to_db = sys.argv[3] == "--dry-run=false"

    db_client = db.market_data_db_client()

    if write_to_db:
        db_client.connect()

    k = len(symbols)
    print(f"Total symbol count: {k}")
    if k > 1:
        results_stdout = {}
        results_dbwrite: list[FcstAnalystPriceTarget] = []
        
        for i, s in enumerate(symbols):
            # due to upstream rate limiter on TipRanks, batch 5 requests at a time every minute
            if not skip_tipranks and i > 4 and i % 5 == 0:
                if write_to_db:
                    write_rows_to_table(db_client, results_dbwrite)
                    results_dbwrite.clear()
                jitter = random.uniform(0, 10)
                interval = 60.5 + jitter
                print(f"Waitng {interval} sec due to TipRanks rate limiter (progress: {i} of {k})")
                time.sleep(interval)

            estimates = ResultPair()

            if not skip_tipranks:
                r = fetch_tipranks_estimates(s, print_stdout=not write_to_db)
                if r.mean is not None and not np.isnan(r.mean) and not np.isnan(r.last_closing_price):
                    # for TipRanks upside potential estimates, we divide the mean over the last closing price because
                    # the median is not available
                    r.upside_potential = r.mean / r.last_closing_price
                    results_stdout[s] = r.upside_potential
                    results_dbwrite.append(r)
                    estimates.tipranks = r

            if s not in const.ETF_SYMBOLS:
                r = fetch_yfinance_estimates(s)
                if r.median is not None and not np.isnan(float(r.median)) and not np.isnan(r.last_closing_price):
                    # for Yahoo Finance upside potential estimates, the formula is slightly different than TipRanks
                    # because the median price estimate IS available. So we divide the median over the last closing
                    # price as more accurate alternate
                    r.upside_potential = r.median / r.last_closing_price
                    results_stdout[s] = r.upside_potential
                    results_dbwrite.append(r)
                    estimates.yfinance = r

            if not write_to_db:
                print(estimates.tipranks)
                print(estimates.yfinance)

        if len(results_dbwrite) > 0:
            # if there is anything else left in the buffer, flush to the database
            write_rows_to_table(db_client, results_dbwrite)

        if skip_tipranks and write_to_db:
            write_rows_to_table(db_client, results_dbwrite)
        else:
            sorted_results_stdout = sorted(results_stdout.items(), key=lambda x:x[1], reverse=True)
            table_header = ["Symbol", "Analyst Upside Potential"]
            row_results_stdout = []
            for k, v in sorted_results_stdout:
                v_formatted = "{0:.3f}".format(v)
                row_results_stdout.append([k, v_formatted])
            print()
            print(tabulate([table_header] + row_results_stdout, headers="firstrow"), "\n")

    else:
        s = symbols[0]
        is_etf = s.upper() in const.ETF_SYMBOLS 
        fetch_analyst_forecasts(s, skip_yfinance=is_etf)

if __name__ == "__main__":
    main()
