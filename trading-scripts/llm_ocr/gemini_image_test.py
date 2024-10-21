import csv
import google.generativeai as genai
import os


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


genai.configure(api_key=os.environ["GEMINI_API_KEY"])
screenshot = genai.upload_file("jd_com_historical_cash_flow.png")
print(f"{screenshot=}")
prompt = """Use the *.png screenshot uploaded via this API for the following prompt:

This is screenshot of a Free Cash Flow (FCF) web page. Notice there is a table with two
columns. Please use both of the columns to extract the FCF data in CSV format from this
screenshot. The CSV generated should have a header row and two columns: the left-most
column should have the dates extracted from the screenshots in YYYY-MM-DD format, and the
right-most column should have the dollar ($) amounts of the FCF values.

The output MUST NOT be in Markdown fomat, i.e. MUST NOT have open or closing triple
backticks (no syntax descriptor either)
"""
model = genai.GenerativeModel("gemini-1.5-flash")
result = model.generate_content(
    [screenshot, "\n\n", prompt]
)
print(f"{result.text=}")

export_text_as_csv(result.text, "gemini_out.csv")
