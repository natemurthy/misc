import os
import pandas as pd
import util

#from typing import Tuple


def cleanup_portfolio_csv(filename: str) -> str:
    fout_filename = f"clean-{filename}.csv"
    with open(filename) as fin, open(fout_filename, 'w') as fout:
        lines = fin.readlines()
        print(filename, lines[-1].replace("\n",""))
        if util.is_etrade(filename):
            fout.writelines(lines[10:-6])
        elif util.is_fidelity(filename):
            fout.writelines(lines[:-5])
    return fout_filename


def _from_fidelity_value_to_float(v: str) -> float:
    if v == "nan":
        return 0.0
    else:
        return float(v.replace("$",""))

def get_total_value(clean_filename) -> float:
    df = pd.read_csv(clean_filename)
    if util.is_etrade(clean_filename):
        return df["Value $"].sum()
    elif util.is_fidelity(clean_filename):
        s = df["Current Value"].apply(lambda v: _from_fidelity_value_to_float(str(v)))
        return s.sum()
    return 0.0
    

def main():
    from os import listdir
    from os.path import isfile, join

    curr_path = os.getcwd()
    files = [f for f in listdir(curr_path) if isfile(join(curr_path, f)) and f.startswith("Portfolio")]

    total = 0
    for f in files:
        clean_fname = cleanup_portfolio_csv(f)
        v = get_total_value(clean_fname)
        print(v)
        total += v

    print("Total Value", f"${total:,.2f}")

   
if __name__ == "__main__":
    main()
