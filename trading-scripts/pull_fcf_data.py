import sys
from playwright.sync_api import sync_playwright


# TODO
# 1. add support for prompting LLM API to extract FCF table data

def main():
    s = sys.argv[1]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        S = s.upper()
        page.goto(f"https://ycharts.com/companies/{S}/free_cash_flow")
        page.screenshot(path=f"fcf_screenshot_{s}.png", full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
