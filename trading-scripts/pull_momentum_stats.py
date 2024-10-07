import db
import util
import numpy as np
import pandas as pd
import random
import sys
import yfinance as yf

from dataclasses import dataclass
from datetime import datetime
from tabulate import tabulate


@dataclass
class HistMomentumStat(db.TableRowStruct):
    sma_period: str
    last_adj_close: float
    time_frame_low: float
    curr_distance_from_low: float
    last_sma: float
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


def calc_sma(df: pd.DataFrame, period: str) -> pd.DataFrame:
    # 200 week SMA (assumes 5 business days in trading week)
    window = 20
    if period.endswith("d"):
        window = int(period[:-1])
    if period.endswith("w"):
        window = int(period[:-1]) * 5
    return df.rolling(window=window).mean()


def get_time_frame_low(series: pd.Series) -> float:
    return float(series.min())


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
            df_sma = calc_sma(df, period).tail()
            print(df.tail())
            print(df_sma)
            sma_last = df_sma.iloc[-1]["Close"]
            fmt_sma_last = "{0:.5f}".format(sma_last)
            print(f"Current {period} SMA: ${fmt_sma_last}")
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
                adj_close = df.iloc[-1]["Adj Close"][S]
                fmt_adj_close = "{0:.5f}".format(adj_close)
                #print(f"Last price: $ last {fmt_last}, adj_close {fmt_adj_close}")
                low = get_time_frame_low(df['Close'][S])
                fmt_low = "{0:.5f}".format(low)
                delta_last_low = ((last_closing_price - low)/low)*100
                fmt_delta_last_low = "{0:.2f}".format(delta_last_low)
                #print(f"Time frame low: {fmt_low}")
                #print(f"Current distance from low: {fmt_delta_last_low} %")
                df_sma = calc_sma(df['Close'][S], period).tail()
                sma_last = df_sma.iloc[-1]
                fmt_sma_last = "{0:.5f}".format(sma_last)
                #print(f"Current {period} SMA: ${fmt_sma_last}")
                momentum_factor = sma_last/last_closing_price
                fmt_momentum_factor = "{0:.2f}".format(momentum_factor)

                if not np.isnan(momentum_factor):
                    results_stdout[S] = momentum_factor
                    m = HistMomentumStat.empty_result("yfinance", S)
                    m.last_closing_price = last_closing_price
                    m.sma_period = period
                    m.last_adj_close = adj_close
                    m.time_frame_low = low
                    m.curr_distance_from_low = delta_last_low
                    m.last_sma = sma_last
                    m.momentum_factor = momentum_factor
                    if not write_to_db:
                        print(f"{s} {fmt_momentum_factor}")
                    else:
                        results_dbwrite.append(m)


def main():
    print(f"Fetching historical price data for '{sys.argv[1]}' and generating momentum stats...")
    symbols = util.get_symbols(sys.argv[1])
    period = sys.argv[2]
    start_date = sys.argv[3] # e.g '2024-04-01'
    end_date = datetime.today().strftime('%Y-%m-%d')
    write_to_db = False
    if len(sys.argv) > 4:
        write_to_db = sys.argv[4] == "--dry-run=false"
    
    db_client = db.market_data_db_client()

    if write_to_db:
        db_client.connect()

    k = len(symbols)
    print(f"Total symbol count: {k}")
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
