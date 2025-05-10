import os
import pandas as pd

from typing import Set


skip_symbols = [
    "CORE**",
    "BRKB",
    "FSRNQ",
]

def extract_symbols(filename: str) -> Set[str]:
    portfolio_all = pd.read_csv(filename)
    portfolio_all = portfolio_all.set_index('Symbol')
    positions = [pos for pos in set(portfolio_all.index.tolist()) \
        if len(pos.split(' ')) < 2 and pos[0].isalpha() and pos not in skip_symbols] # filter out invalid positions

    if 'BRK.B' in positions:
        i = positions.index('BRK.B')
        positions[i] = 'BRK-B'

    return set(positions)


def main():
    from os import listdir
    from os.path import isfile, join

    existing_symbols = []
    with open("my_sorted_symbols.txt", 'r') as fin:
        for s in fin:
            existing_symbols.append(s.replace("\n",""))

    print(existing_symbols)

    curr_path = os.getcwd()
    files = [f for f in listdir(curr_path) if isfile(join(curr_path, f)) and f.startswith("clean-Portfolio")]

    my_symbols = set(existing_symbols)
    for f in files:
        my_symbols |= extract_symbols(f)

    print()
    print("Symbol count:", len(my_symbols))
    my_sorted_symbols = sorted(my_symbols)
    print(my_sorted_symbols)

    with open("my_sorted_symbols.txt", 'w') as fout:
        for s in my_sorted_symbols:
            fout.write(s+"\n")

if __name__ == "__main__":
    main()
