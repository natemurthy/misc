import google.generativeai as genai
import os
import util
import sys

from playwright.sync_api import sync_playwright


prompt = """Use the *.png screenshot uploaded via this API for the following prompt:

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
        page.goto(url_source)
        page.screenshot(path=output_filename, full_page=True)
        browser.close()
        return output_filename


def extract_fcf_table_data(s: str, input_filename: str) -> str:
    global prompt
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    screenshot = genai.upload_file(input_filename)
    print("info_extract_fcf_table_data:", f"{screenshot=}")
    model = genai.GenerativeModel("gemini-1.5-flash")
    result = model.generate_content(
        [screenshot, "\n\n", prompt]
    )
    print(f"{result.text=}")
    util.export_text_as_csv(result.text, f"gemini_out_{s}.csv")
    return result.text


def main():
    s = sys.argv[1] # ticker symbol
    f = capture_fcf_screenshot(s)
    extract_fcf_table_data(s, f)
    

if __name__ == "__main__":
    main()
