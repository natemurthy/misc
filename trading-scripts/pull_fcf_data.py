import const
import datetime as dt
import db
import google.generativeai as genai
import os
import sys
import util

from dataclasses import dataclass
from playwright.sync_api import sync_playwright


DATE_FMT = "%Y-%m-%d"

@dataclass
class HistFreeCashFlow:
    id: int | None
    created_at: dt.datetime | None
    symbol: str
    release_date: dt.date
    ycharts_raw_fcf: str
    fcf_usd: int

    @staticmethod
    def empty_result(s: str):
        return HistFreeCashFlow(
            id=None,
            created_at=None,
            symbol=s.upper(),
            release_date=util.today_us_pacific(),
            ycharts_raw_fcf="-infinity",
            fcf_usd=-sys.maxsize - 1,
        )

def write_rows_to_table(c: db.PostgresClient, data: list[HistFreeCashFlow]) -> None:
    res = c.insert(
        schema_name="timeseries",
        table_name="hist_free_cash_flow",
        rows=data,
    )
    print(f"info_write_rows_to_table: {res}")


prompt = """Use the *.png screenshot file uploaded via this API for the following prompt:

This is screenshot of a Free Cash Flow (FCF) web page. Notice there is a table with two
columns. Please use both of the columns to extract the FCF data in CSV format from this
screenshot. The CSV generated should have a header row and two columns: the left-most
column should have the dates extracted from the screenshots in YYYY-MM-DD format, and the
right-most column should have the dollar ($) amounts of the FCF values.

The output MUST NOT be in Markdown fomat, i.e. MUST NOT have open or closing triple
backticks (no syntax descriptor either)
"""

def capture_fcf_screenshot(s: str) -> str:
    S = s.upper()
    url_source = f"https://ycharts.com/companies/{S}/free_cash_flow"
    output_filename = f"fcf_screenshot_{s}.png"
    print("info_capture_fcf_screenshot:", url_source)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url_source) # NOTE: this might timeout after 30sec
        page.screenshot(path=output_filename, full_page=True)
        browser.close()
        return output_filename


def extract_fcf_table_data(input_filename: str) -> str:
    # NOTE the LLM has observed to have data quality issues extracting the fcf data
    global prompt
    genai.configure(api_key=os.environ["GEMINI_API_KEY"]) # https://aistudio.google.com/app/apikey
    screenshot = genai.upload_file(input_filename)
    print("info_extract_fcf_table_data:", f"{screenshot=}")
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content([screenshot, "\n\n", prompt])
    return result.text


def str_to_usd(ycharts_raw_fcf: str) -> int:
    res = 0.0
    if ycharts_raw_fcf.endswith("K"):
        v = ycharts_raw_fcf.replace("K","")
        res = float(v)*1e6
    if ycharts_raw_fcf.endswith("M"):
        v = ycharts_raw_fcf.replace("M","")
        res = float(v)*1e6
    if ycharts_raw_fcf.endswith("B"):
        v = ycharts_raw_fcf.replace("B","")
        res = float(v)*1e9
    return round(res)


def str_to_date(ycharts_date: str) -> dt.date:
    try:
        return dt.datetime.strptime(ycharts_date, DATE_FMT).date()
    except ValueError:
        # LLM will not always properly extract the dates, so need to revise them manually,
        # e.g. 2023-04-31 is out of bounds, and so is 2018-02-29
        if ycharts_date.endswith("-29"):
            rev_date = ycharts_date.replace("-29","-28")
            return dt.datetime.strptime(rev_date, DATE_FMT).date()
        if ycharts_date.endswith("-31"):
            rev_date = ycharts_date.replace("-31","-30")
            return dt.datetime.strptime(rev_date, DATE_FMT).date()


def main():
    print(f"Fetching free cash flow data for '{sys.argv[1]}'")
    symbols = util.get_symbols(sys.argv[1])
    write_to_db = False
    if len(sys.argv) > 2:
        write_to_db = sys.argv[2] == "--dry-run=false"

    db_client = db.market_data_db_client()

    if write_to_db:
        db_client.connect()

    k = len(symbols)
    print("info_main:", f"total symbol count: {k}")
    if k > 1:
        results_dbwrite: list[HistFreeCashFlow] = []
        num_workers, worker_index = util.get_num_workers_and_worker_index()
        for i in util.get_symbol_ranges_for_worker(worker_index, num_workers, k):
            s = symbols[i]
            print("info_main:", f"symbol_index = {i}")
            if s not in const.ETF_SYMBOLS:
                png = capture_fcf_screenshot(s)
                data = extract_fcf_table_data(png).splitlines()
                for i, d in enumerate(data):
                    if i == 0: # skip Date,Value header
                        continue
                    date_value = d.split(",")
                    if len(date_value) == 2: # have to check because LLM might not produce correctly
                        fcf = HistFreeCashFlow.empty_result(s)
                        try:
                            fcf.release_date=str_to_date(date_value[0])
                            fcf. ycharts_raw_fcf=date_value[1]
                            fcf.fcf_usd=str_to_usd(date_value[1]) # may raise error if symbol has bad FCF data
                            results_dbwrite.append(fcf)
                        except ValueError as ex:
                            print("error_main:", f"err={ex}", f"skipping={fcf}")
                            continue

                if write_to_db and len(results_dbwrite) > 0:
                    # if there is anything else left in the buffer, flush to the database
                    write_rows_to_table(db_client, results_dbwrite)
                else:
                    for d in results_dbwrite:
                        print(d.release_date, d.ycharts_raw_fcf, d.fcf_usd)
                results_dbwrite.clear()
    else:
        s = symbols[0]
        if s not in const.ETF_SYMBOLS:
            png = capture_fcf_screenshot(s)
            data = extract_fcf_table_data(png).splitlines()
            for d in data:
                print(d)

    
if __name__ == "__main__":
    main()
