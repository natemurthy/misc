import const
import csv
import datetime as dt
import os
import random

from pytickersymbols import PyTickerSymbols
from typing import Iterable

# ---------------------------------------------------------------------------------------------------------------------
# Date/Time helpers
# ---------------------------------------------------------------------------------------------------------------------

def today_local(tz) -> dt.date:
    """Get today's date for a given time zone"""
    return dt.datetime.now(tz).date()


def today_us_pacific() -> dt.date:
    """Get today's date in US/Pacific timezone"""
    return today_local(const.TZ_US_PACIFIC)


# ---------------------------------------------------------------------------------------------------------------------
# String/Text manipulation helpers
# ---------------------------------------------------------------------------------------------------------------------

def export_text_as_csv(text, filename):
    """Exports text to a CSV file.

    Args:
        text (str): The text to export.
        filename (str): The name of the CSV file to create.
    """
    lines = text.splitlines()
    rows = [line.split(',') for line in lines]
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


# ---------------------------------------------------------------------------------------------------------------------
# Web helpers
# ---------------------------------------------------------------------------------------------------------------------

def get_random_user_agent_header() -> dict[str,str]:
    """Pick a random user-agent header to spoof browser requests from web scraper"""
    i = random.randint(0,len(const.USER_AGENT_HEADERS)-1)
    return const.USER_AGENT_HEADERS[i]


# ---------------------------------------------------------------------------------------------------------------------
# Portfolio data helpers
# ---------------------------------------------------------------------------------------------------------------------

def is_etrade(filename: str) -> bool:
    """Return True if file (based on name) is an Etrade portfolio dump CSV file"""
    return "PortfolioDownload" in filename


def is_fidelity(filename: str) -> bool:
    """Return True if file is a Fidelity portfolio dump CSV file"""
    return "Portfolio_Positions_" in filename


pytickrs = PyTickerSymbols()

spx = pytickrs.get_stocks_by_index('S&P 500')
ndx = pytickrs.get_stocks_by_index('NASDAQ 100')
dji = pytickrs.get_stocks_by_index('DOWN JONES')

def _merge_dedup(*indices) -> list[str]:
  all = []
  for ix in indices:
    all += [s['symbol'] for s in list(ix)]
  return sorted(list(set(all)))


def get_all_symbols_from_major_indices() -> list[str]:
    return _merge_dedup(spx, ndx, dji)


def get_symbols(arg: str) -> list[str]:
    """Given the sys.arg input passed to arg, either read symbols only from my_sorted_symbols.txt file or get all
    symbols listed on the major indices and combine, dedup, and sort those with my_sorted_symbols
    """
    symbols = []
    if arg == const.MY_SORTED_SYMBOLS or arg == "all":
        #print("debug_get_symbols", f"Loading symbols from {const.MY_SORTED_SYMBOLS}")
        f = open(const.MY_SORTED_SYMBOLS, 'r')
        lines = f.readlines()
        for l in lines:
            s = l.replace("\n","")
            symbols.append(s)
        if arg == "all":
            #print("debug_get_symbols", f"Loading symbols from major indices and combining with {const.MY_SORTED_SYMBOLS}")
            return sorted(list(set(symbols + get_all_symbols_from_major_indices())))
    else:
        return [arg]
    return symbols


# ---------------------------------------------------------------------------------------------------------------------
# GCP helpers
# ---------------------------------------------------------------------------------------------------------------------

def get_symbol_ranges_for_worker(worker_index: int, num_workers: int, num_symbols: int) -> Iterable[int]:
    """This is a Cloud Run helper method for determining a range of symbols assigned to an individual worker identified
    by its index. This function is also somewhat of a portfolio data helper."""
    if worker_index >= num_workers:
        raise ValueError(
            "worker_index must be less than num_workers. " f"worker_index={worker_index}, num_workers={num_workers}"
        )
    range_len = num_symbols // num_workers
    remainder = num_symbols % num_workers
    if worker_index < remainder:
        i = worker_index * (range_len + 1)
        j = i + range_len + 1
    else:
        i = worker_index * range_len + remainder
        j = i + range_len
    return range(i, j)


def get_num_workers_and_worker_index() -> tuple[int, int]:
    """Find the total number of workers and the worker index for a given Clour Run execution"""
    num_workers = int(os.getenv("CLOUD_RUN_TASK_COUNT", 1))
    worker_index = int(os.getenv("CLOUD_RUN_TASK_INDEX", 0))
    return num_workers, worker_index

