#!/usr/bin/env python3

from pathlib import Path
import pandas as pd


def main():
    current_dir = Path.cwd()
    all_final_iters = current_dir.rglob('final_iter.csv')
    dfs = []
    for csv in all_final_iters:
        df = pd.read_csv(csv)
        dfs.append(df)
    big_df = pd.concat(dfs)
    big_df.to_csv(current_dir/'all_final_iter.csv')


if __name__ == '__main__':
    main()
