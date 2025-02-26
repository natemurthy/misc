import db
import math
import numpy as np
import util
import pandas as pd
import random
import sys
import yfinance as yf

from dataclasses import dataclass
from dateutil.relativedelta import relativedelta
from tabulate import tabulate


@dataclass
class HistMomentumStat(db.TableRowStruct):
    sma_period: str
    last_adj_close: float
    time_frame_low: float
    curr_distance_from_low: float
    last_sma: float
    last_rsi: float
    momentum_factor: float

    @staticmethod
    def empty_result(source: db.SourceLiteral, s: str):
        nan = float("nan")
        return HistMomentumStat(
            id=None,
            created_at=None,
            source=source,
            symbol=s.upper(),
            trading_day=util.today_us_pacific(),
            last_closing_price=nan,
            sma_period="",
            last_adj_close=nan,
            time_frame_low=nan,
            curr_distance_from_low=nan,
            last_sma=nan,
            last_rsi=nan,
            momentum_factor=nan,
        )


def write_rows_to_table(c: db.PostgresClient, data: list[HistMomentumStat]) -> None:
    ids_written = c.insert(
        schema_name="timeseries",
        table_name="hist_momentum_stat",
        rows=data,
    )
    print(f"Rows written to database: count={len(ids_written)}, last_row_id={ids_written[-1]}")


def download_yf_data(symbols:list[str], start: str, end: str) ->  pd.DataFrame:
    df = yf.download(symbols, start=start, end=end)
    print(f"Last price date: {df.iloc[-1].name}")
    return df


def days_in_window(period: str) -> int:
    ndays = 20
    if period.endswith("d"):
        ndays = int(period[:-1])
    if period.endswith("w"):
        ndays = int(period[:-1]) * 5
    return ndays


def calc_sma(df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Calculate the simple-moving average (SMA) over a given period

    Args:
        df: time series of one symbol
        period: 20, 50, 100, 200 {d,w}

    Returns:
        tail of the SMA data frame
    """
    # 200 week SMA (assumes 5 business days in trading week)
    window = days_in_window(period)
    return df.rolling(window=window).mean().tail()


def calc_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the relative strength index (RSI) of time series, implementation borrowed from

    https://medium.com/@huzaifazahoor654/how-to-calculate-rsi-in-python-a-step-by-step-guide-06b96a2da25e

    Ags:
        df: timeseries of one symbol

    Returns:
        tail of RSI data frame
    """
    df_copy = df.copy()
    df_copy['Change'] = df_copy.diff()
    df_copy['Gain'] = pd.Series(np.where(df_copy['Change'] > 0, df_copy['Change'], 0))
    df_copy['Loss'] = pd.Series(np.where(df_copy['Change'] < 0, -df_copy['Change'], 0))
    period = 12 # use 12 (average of 10 days over two business weeks, and 14 days over two calendar weeks)
    df_copy['Avg Gain'] = df_copy['Gain'].rolling(window=period).mean()
    df_copy['Avg Loss'] = df_copy['Loss'].rolling(window=period).mean()
    df_copy['RS'] = df_copy['Avg Gain'] / df_copy['Avg Loss']
    df_copy['RSI'] = 100 - (100 / (1 + df_copy['RS']))
    return df_copy['RSI'].tail()


def get_time_frame_low(series: pd.Series) -> float:
    return float(series.min())


def get_sma_period_from_task_index() -> str:
    _, i = util.get_num_workers_and_worker_index()
    match i:
        case 0: return "20d"
        case 1: return "50d"
        case 2: return "100d"
        case 3: return "200d"
        case 4: return "20w"
        case 5: return "50w"
        case 6: return "100w"
        case 7: return "200w"
        case _: return ""


results_stdout = {}
results_dbwrite: list[HistMomentumStat] = []

def get_momentum_stats(
    symbols: list[str],
    period: str,
    df: pd.DataFrame,
    db_client: db.PostgresClient,
    write_to_db: bool = False,
) -> None:
    global results_stdout, results_dbwrite
    last = df.iloc[-1]["Close"]
    match type(last):
        case np.float64:
            # print for just one symbol
            fmt_last = "{0:.5f}".format(last)
            fmt_adj_close = "{0:.5f}".format(df.iloc[-1]["Adj Close"])
            print(f"Last price: $ last {fmt_last}, adj_close {fmt_adj_close}")
            low = get_time_frame_low(df['Low'])
            fmt_low = "{0:.5f}".format(low)
            delta_last_low = ((last - low)/low)*100
            fmt_delta_last_low = "{0:.2f}".format(delta_last_low)
            print(f"Time frame low: {fmt_low}")
            print(f"Current distance from low: {fmt_delta_last_low} %")
            df_sma = calc_sma(df['Close'], period)
            df_rsi = calc_rsi(df['Close'])
            print(df.tail())
            print(df_sma)
            print(df_rsi)
            sma_last = df_sma.iloc[-1]
            fmt_sma_last = "{0:.5f}".format(sma_last)
            rsi_last = df_rsi.iloc[-1]
            fmt_rsi_last = "{0:.5f}".format(rsi_last)
            print(f"Current {period} SMA: ${fmt_sma_last}")
            print(f"Current RSI: {fmt_rsi_last}")
            upside_momentum = sma_last/last
            fmt_upside_momentum = "{0:.5f}".format(upside_momentum)
            print(f"Upside momentum: {fmt_upside_momentum}")
        case pd.Series:
            # print for multiple symbols
            for i, s in enumerate(symbols):
                S = s.upper()

                if len(results_dbwrite) > 10 and i % random.randint(3,8) == 0:
                    write_rows_to_table(db_client, results_dbwrite)
                    print(f"Progress: {i} of {len(symbols)}")
                    results_dbwrite.clear()

                #print("-------------------------------------------------------------")
                #print(f"Momentum stats for {S}")
                last_closing_price = float(last[S])
                fmt_last = "{0:.5f}".format(last_closing_price)
                #adj_close = df.iloc[-1]["Adj Close"][S]
                #fmt_adj_close = "{0:.5f}".format(adj_close)
                #print(f"Last price: $ last {fmt_last}, adj_close {fmt_adj_close}")
                low = get_time_frame_low(df['Close'][S])
                fmt_low = "{0:.5f}".format(low)
                delta_last_low = ((last_closing_price - low)/low)*100
                fmt_delta_last_low = "{0:.2f}".format(delta_last_low)
                #print(f"Time frame low: {fmt_low}")
                #print(f"Current distance from low: {fmt_delta_last_low} %")
                df_sma = calc_sma(df['Close'][S], period)
                df_rsi = calc_rsi(df['Close'][S])
                sma_last = df_sma.iloc[-1]
                rsi_last = df_rsi.iloc[-1]
                fmt_sma_last = "{0:.5f}".format(sma_last)
                #print(f"Current {period} SMA: ${fmt_sma_last}")
                momentum_factor = sma_last/last_closing_price
                fmt_momentum_factor = "{0:.2f}".format(momentum_factor)

                if not math.isnan(momentum_factor):
                    results_stdout[S] = momentum_factor
                    m = HistMomentumStat.empty_result("yfinance", S)
                    m.last_closing_price = last_closing_price
                    m.sma_period = period
                    #m.last_adj_close = adj_close
                    m.time_frame_low = low
                    m.curr_distance_from_low = delta_last_low
                    m.last_sma = sma_last
                    if period == "20d":
                        # only calculate RSI for SMA period that is most similar to time window /
                        # horizon of RSI calc (12 days, is closest to 20 days). Otherwise there
                        # will some duplicate RSI values for all the other SMA periods
                        m.last_rsi = rsi_last
                    m.momentum_factor = momentum_factor
                    if not write_to_db:
                        print(s, fmt_momentum_factor)
                    else:
                        results_dbwrite.append(m)


def main():
    print(f"info_main: fetching historical price data for '{sys.argv[1]}' and generating momentum stats...")
    symbols = util.get_symbols(sys.argv[1])
    write_to_db = False
    if len(sys.argv) > 2:
        write_to_db = sys.argv[2] == "--dry-run=false"

    period = get_sma_period_from_task_index()
    d = days_in_window(period)
    today = util.today_us_pacific()
    start_date = (today - relativedelta(days=int(d*1.5))).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
        
    db_client = db.market_data_db_client()

    if write_to_db:
        db_client.connect()

    k = len(symbols)
    print(f"info_main: total symbol count = {k}, sma_period = {period}")
    if k > 1:
        global results_stdout, results_dbwrite
        df = download_yf_data(symbols, start_date, end_date)
        get_momentum_stats(symbols, period, df, db_client, write_to_db=write_to_db)
        if write_to_db and len(results_dbwrite) > 0:
            # if there is anything else left in the buffer, flush to the database
            write_rows_to_table(db_client, results_dbwrite)
        else:
            sorted_results = sorted(results_stdout.items(), key=lambda x:x[1], reverse=True)
            table_header = ["Symbol", "Momentum Factor"]
            row_results = []
            for k, v in sorted_results:
                v_formatted = "{0:.2f}".format(v)
                row_results.append([k, v_formatted])
            print()
            print(tabulate([table_header] + row_results, headers="firstrow"), "\n")
    else:
        df = download_yf_data(symbols, start_date, end_date)
        get_momentum_stats(symbols, period, df, db_client, write_to_db=False)


if __name__ == "__main__":
    main()
