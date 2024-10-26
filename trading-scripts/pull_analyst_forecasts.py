import const
import datetime as dt
import db
import math
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
    median: float | None # Yahoo Finance only
    ratings_count: int | None # TipRanks only
    
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
            ratings_count=None,
        )

def write_rows_to_table(c: db.PostgresClient, data: list[FcstAnalystPriceTarget]) -> None:
    ids_written = c.insert(
        schema_name="timeseries",
        table_name="fcst_analyst_price_target",
        rows=data,
    )
    print("debug_write_rows_to_table:", f"data saved to db (count={len(ids_written)}, last_row_id={ids_written[-1]})")


def get_ratings_count_from_html(s: str, span_mr2: ResultSet) -> int:
    try:
        return int(span_mr2[0].contents[0]) + \
            int(span_mr2[1].contents[0]) + \
            int(span_mr2[2].contents[0])
    except Exception as ex:
        print("error_get_ratings_count_from_html:", f"symbol={s.upper()}", f"err={ex}", f"span_mr2={span_mr2}")
        return 0


def get_target_from_html(s: str, tr: ResultSet, i: int) -> float:
    try:
        return float(tr[0].find_all('td')[i].find_all('span')[1].contents[0].replace("$", "").replace(",", ""))
    except Exception as ex:
        print("error_get_target_from_html:", f"symbol={s.upper()}", f"err={ex}", f"tr={tr}")
        return 0.0


def fetch_tipranks_estimates(s: str, print_stdout: bool = True) -> FcstAnalystPriceTarget:
    """Analyst estimates from TipRanks are available from one of two URL paths dependening on asset type:

        For stocks: https://www.tipranks.com/stocks/{s.lower()}/forecast
        For ETFs:   https://www.tipranks.com/etf/{s.lower()}/forecast

    Where s.lower() is a ticker symbol in lower case. These may be visited with a typical web browser and are often
    restricted / limited to view after a small number of page visits.

    Because TipRanks loads last closing price via an asyncronous client-side rendering, the true current price may
    not reliably be available via page scraping. So this will also use Yahoo Finance for that number.
    """
    S = s.upper()
    k, cur, potential, lo, avg, hi = 0, 0, 0 ,0 ,0, 0
    asset_type = "etf" if S in const.ETF_SYMBOLS else "stocks"
    url = f"https://www.tipranks.com/{asset_type}/{s.lower()}/forecast"
    res = FcstAnalystPriceTarget.empty_result("tipranks", S)
    print("debug_fetch_tipranks_estimates:", f"symbol={S}")
    try:
        h = util.get_random_user_agent_header()
        r = requests.get(url, headers=h)
    except Exception as ex:
        print(
            "error_fetch_tipranks_estimates:",
            f"symbol='{S}'",
            f"err='{ex}'",
            f"http_resp='{r}'",
            f"req_header='{h}'",
        )
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
        k = get_ratings_count_from_html(s, span_mr2)
        res.ratings_count = k
        # NOTE not a reliable source of last price, value might cached or "stuck"
        #if asset_type == "etf":
            #cur = float(soup.find_all("span", {"class": "fontWeightsemibold colorblack"})[21].contents[0].replace("$", "").replace(",", ""))
        #if asset_type == "stocks":
            #cur = float(soup.find_all("span", {"class": "fontWeightsemibold colorblack"})[22].contents[0].replace("$", "").replace(",", ""))
        hi = get_target_from_html(s, tr, 0)
        avg = get_target_from_html(s, tr, 2)
        lo = get_target_from_html(s, tr, 4)
        res.low = lo
        res.high = hi
        res.mean = avg
    except Exception as ex:
        print(
            "error_fetch_tipranks_estimates:",
            f"symbol={S}",
            f"err='{ex}'",
            f"reason='html parsing error'",
            f"http_resp='{r}'",
            f"req_header={h}",
        )
        return res
    if print_stdout:
        print("TipRanks ratings count:", k)
    ticker_info = {}
    try:
        ticker_info = yf.Ticker(S).info
        if ticker_info["quoteType"] == "EQUITY":
            cur = ticker_info["currentPrice"]
        if ticker_info["quoteType"] == "ETF":
            cur = (ticker_info["bid"]+ticker_info["ask"])/2.0
        res.last_closing_price = cur
    except Exception as ex:
        print(
            "error_fetch_tipranks_estimates:",
            f"symbol={S}",
            f"err='{ex}'",
            f"reason='no latest price available from yfinance'",
        )
    if avg != 0 and cur != 0:
        # for TipRanks upside potential estimates, we divide the mean over the last closing price because
        # the median is not available
        res.upside_potential = avg / cur
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
        if res.median is not None and not math.isnan(float(res.median)) and not math.isnan(res.last_closing_price):
            # for Yahoo Finance upside potential estimates, the formula is slightly different than TipRanks
            # because the median price estimate IS available. So we divide the median over the last closing
            # price as more accurate alternate
            res.upside_potential = res.median / res.last_closing_price
    except Exception as ex:
        print("error_fetch_yfinance_estimates:",f"symbol={s.upper()}",  f"err='{ex}'")
    return res


def fetch_analyst_forecasts(s: str, skip_tipranks: bool = False, skip_yfinance: bool = False):
    ticker_data = yf.Ticker(s)
    short_name: str = ticker_data.info["shortName"] 
    try:
        curr_price = ticker_data.info["currentPrice"]
    except KeyError:
        # This occurs for SPY, have not checked if this happens for all ETF symbols
        curr_price = ticker_data.info["ask"]
    summary: str = f"Forecasts for {short_name} (symbol: {s.upper()}, last: ${curr_price})"
    print(summary)

    if not skip_tipranks:
        r = fetch_tipranks_estimates(s)
        if not math.isnan(r.mean):
            print(r)
        else:
            print("No TipRanks data available")

    if not skip_yfinance:
        r = fetch_yfinance_estimates(s)
        if not math.isnan(r.mean):
            print(r)
        else:
            print("No Yahoo Finance data available")


def main():
    print("info_main:", f"fetching analyst price targets/estimates for '{sys.argv[1]}' (12-month forecast)")
    symbols = util.get_symbols(sys.argv[1])
    source = "yfinance"
    write_to_db = False
    if len(sys.argv) > 2:
        source = sys.argv[2] # yfinance (default) or tipranks
    if len(sys.argv) > 3:
        write_to_db = sys.argv[3] == "--dry-run=false"

    db_client = db.market_data_db_client()

    if write_to_db:
        db_client.connect()

    k = len(symbols)
    print("info_main:", f"total symbol count: {k}")
    if k > 1:
        results_stdout = {}
        results_dbwrite: list[FcstAnalystPriceTarget] = []

        if source == "yfinance":
            print("info_main:", "pulling analyst price targets from yfinance")
            for s in symbols:
                if s not in const.ETF_SYMBOLS:
                    r = fetch_yfinance_estimates(s)
                    if not write_to_db:
                        print(r)
                    if not math.isnan(r.upside_potential):
                        results_stdout[f"yfinance:{s}"] = r.upside_potential
                        results_dbwrite.append(r)
            if write_to_db:
                print("info_main:", f"writing yfinance analyst data to db (row_count = {len(results_dbwrite)})")
                write_rows_to_table(db_client, results_dbwrite)
                results_dbwrite.clear()

        if source == "tipranks":
            print("info_main:", "pulling analyst price targets from tipranks")
            num_workers, worker_index = util.get_num_workers_and_worker_index()
            for i in util.get_symbol_ranges_for_worker(worker_index, num_workers, k):
                # due to upstream rate limiter on TipRanks, batch 5 requests at a time every minute
                s = symbols[i]
                if i > 4 and i % 5 == 0:
                    if write_to_db and len(results_dbwrite) > 0:
                        print("info_main:", f"writing tipranks analyst data to db (row_count = {len(results_dbwrite)})")
                        write_rows_to_table(db_client, results_dbwrite)
                        results_dbwrite.clear()
                    jitter = random.uniform(0, 10)
                    interval = 60.5 + jitter
                    print("info_main:", f"waitng {interval} sec due to tipranks rate limiter")
                    time.sleep(interval)

                print("info_main:", f"symbol_index = {i}")
                r = fetch_tipranks_estimates(s, print_stdout=not write_to_db)
                if not write_to_db:
                    print(r)
                if not math.isnan(r.upside_potential):
                    results_stdout[f"tipranks:{s}"] = r.upside_potential
                    results_dbwrite.append(r)

        if write_to_db and len(results_dbwrite) > 0:
            # if there is anything else left in the buffer, flush to the database
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
