import db
import util
import sys

from dataclasses import dataclass


@dataclass
class Holdings:
    symbol: str


def write_rows_to_table(c: db.PostgresClient, data: list[Holdings]) -> None:
    res = c.insert(
        schema_name="portfolio",
        table_name="holdings",
        rows=data,
    )
    print(type(res))
    print(f"Rows written to database: {res}")


def main():
    print(f"Uploading '{sys.argv[1]}'")
    symbols = util.get_symbols(sys.argv[1])
    write_to_db = False
    if len(sys.argv) > 2:
        write_to_db = sys.argv[2] == "--dry-run=false"

    db_client = db.market_data_db_client()

    if write_to_db:
        db_client.connect()
    
    k = len(symbols)
    print(f"Total symbol count: {k}")

    results_dbwrite: list[Holdings] = []
    for s in symbols:
        h = Holdings(s)
        results_dbwrite.append(h)

    if write_to_db and len(results_dbwrite) > 0:
        write_rows_to_table(db_client, results_dbwrite)

if __name__ == "__main__":
    main()
