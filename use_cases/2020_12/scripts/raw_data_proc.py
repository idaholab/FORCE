#!/usr/bin/env python3
"""Raw data processing module for EPRI."""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
from functools import reduce

# Global Constants
YEARS = np.arange(2015, 2055, 5)
HOURS = np.arange(1, 8761, 1)
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath("train")
DATA_DIR = BASE_DIR.joinpath("data", "from_EPRI")


def read_workbook(file_path: Path) -> dict:
    """
    Return dictionary of workbook sheets mapped to dataframes.

    @In: file_name, Path, a POSIXPath to workbook
    @Out: dictionary, a dictionary containing sheetname: dataframe
          for each sheet in workbook.
    """
    return pd.read_excel(
        io=DATA_DIR.joinpath(file_path.name),
        sheet_name=None,
        index_col=0,
        engine='xlrd'
    )


def format_ts(key: str, dat: pd.DataFrame) -> pd.DataFrame:
    """
    Return indexed time-series dataframe.

    @In: key, str, A string containing sheet-name from workbook.
    @In: dat, pd.DataFrame, A dataframe containing data from
         respective sheet.
    @Out: pd.DataFrame, a fully indexed dataframe
    """
    # Each sheet name contains "<STATE>-<VARIABLE>"
    state = key.split('-')[0]
    # Make all variable naming consistent
    var = key.split('-')[1].replace(" ", "").upper()
    # Index should fill state x years x hours ≅ 70,080 obs.
    new_idx = pd.MultiIndex.from_product(
        [[state], YEARS, HOURS],
        names=['state', 'year', 'hour']
    )
    # Some data contains missing indices, make those zero
    vals = list(dat.reindex(HOURS, fill_value=0).unstack())
    # Each column should have 8760 rows (hours in year).
    return pd.DataFrame({var: vals}, index=new_idx)


def main():
    """Driver function."""
    parser = argparse.ArgumentParser(
        description="Raw data processing script for EPRI."
    )
    parser.add_argument(
        "--ln", action="store_true",
        help="Transform all numerical data using a natural log."
    )
    parser.add_argument(
        "path", type=Path, help="Specify which state data to visualize."
    )
    args = parser.parse_args()

    workbook = read_workbook(args.path)
    dats = [format_ts(k, d) for k, d in workbook.items()]

    # Combine all data into 1 dataframe to split off by year.
    # The data should contain 140,160 rows. (70,080 * Num of States)
    final_dat = reduce(lambda x, y: x.combine_first(y), dats)

    # Transform data using natural log.
    if args.ln:
        final_dat = final_dat.transform(lambda x: np.log(x))

    case = args.path.stem.lower()
    for state in ["OH", "IL"]:
        for i, key in enumerate(YEARS):
            output_path = TRAIN_DIR.joinpath(case, state, f"Data_{i+1}.csv")
            final_dat.loc[state, key, :].to_csv(
                path_or_buf=output_path,
                index_label=['STATE', 'YEAR', 'HOUR']
            )


if __name__ == '__main__':
    main()
