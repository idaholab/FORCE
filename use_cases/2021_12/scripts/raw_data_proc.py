#!/usr/bin/env python
"""Raw data processing module for EPRI."""
# Internal Libraries
import argparse
from pathlib import Path
from functools import reduce

# External Libraries
import pandas as pd
import numpy as np


# Global Constants
YEARS = np.arange(2015, 2055, 5)
HOURS = np.arange(1, 8761, 1)
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath("train")
DATA_DIR = BASE_DIR.joinpath("data", "from_EPRI")

assert BASE_DIR.is_dir(), f"{BASE_DIR} doesn't exist!"
assert TRAIN_DIR.is_dir(), f"{TRAIN_DIR} doesn't exist!"
assert DATA_DIR.is_dir(), f"{DATA_DIR} doesn't exist!"


def read_workbook(file_path: Path, sheet=None, **kwargs):
    """
    Return dictionary of workbook sheets mapped to dataframes.

    @In: file_name, Path, a POSIXPath to workbook
    @Out: dictionary or pd.Dataframe
    """
    return pd.read_excel(
        io=DATA_DIR.joinpath(file_path.name),
        sheet_name=sheet,
        index_col=0,
        engine='openpyxl',
        **kwargs
    )


def format_ts(key: str, dat: pd.DataFrame) -> pd.DataFrame:
    """
    Return indexed time-series dataframe.

    @In: key, str, A string containing sheet-name from workbook.
    @In: dat, pd.DataFrame, A dataframe containing data from respective sheet.
    @Out: pd.DataFrame, a fully indexed dataframe
    """
    dat = dat.fillna(0)
    # Each sheet name contains "<STATE>_<VARIABLE>"
    state = key.split('_')[0]
    # Make all variable naming consistent - Max split 1
    var = key.split('_', 1)[1].replace(" ", "").upper()
    # Index should fill state x years x hours ≅ 70,080 obs.
    new_idx = pd.MultiIndex.from_product([[state], YEARS, HOURS], names=['STATE', 'YEAR', 'HOUR'])
    # Some data contains missing indices, make those zero
    vals = list(dat.reindex(index=HOURS, fill_value=0).unstack())
    # Each column should have 8760 rows (hours in year).
    return pd.DataFrame({var: vals}, index=new_idx)


def main():
    """Driver function."""
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    # Should either be 'ny_default_load' or 'ny_ces_load'
    case = args.path.stem.lower()
    # We need different data depending on the case
    sheets = ['Reference - No Storage']
    if 'ces' in case:
        sheets = ['CES - No Storage']

    # Combine all data into 1 dataframe to split off by year.
    # The data should contain (70,080 * Num of States) rows.
    workbook = read_workbook(args.path)
    dats = [format_ts(k, d) for k, d in workbook.items()]
    final_dat = reduce(lambda x, y: x.combine_first(y), dats)

    # Let's grab the wind/solar capacity for our respective case
    gen_xlsx = DATA_DIR/'Generation.xlsx'
    capacity_wb = read_workbook(gen_xlsx, sheet='Capacity', usecols='A:P')
    # We want capacity as we will be transforming the raw wind/solar generation
    # data into '% of capacity generated'. We will be training the ARMAs on
    # that metric and not the orginal raw data.
    wind_cap = capacity_wb.loc[sheets[0]]['Wind']
    solar_cap = capacity_wb.loc[sheets[0]][['Utility Scale PV', 'Rooftop Solar']].sum()

    wind_wb = read_workbook(gen_xlsx, sheet=sheets)
    for _, dat in wind_wb.items():
        df = dat.T.rename_axis("HOUR").reset_index()
        df = df.rename(columns={"Wind": "WIND"})
        df = df.replace('Eps', 0)
        # We are combining Utility PV and Rooftop PV into one SOLAR variable
        df['SOLAR'] = (df['Utility Scale Solar'] + df['Rooftop PV']) / solar_cap
        df['WIND'] = df['WIND'] / wind_cap
        df = df[['WIND', 'SOLAR']]
        new_idx = pd.MultiIndex.from_product([['NY'], HOURS], names=['STATE', 'HOUR'])
        df = df.set_index(new_idx)

    # This is a comment for anyone in the future trying to recreate:
    # We ultimately decided to only use the last year of data (2050)
    # because we only had 2050 data for WIND and SOLAR. So we need to filter
    # 'TOTALLOAD' to only be the last year. This undoes quite a bit of
    # the work done earler in the script, so if that part is confusing just
    # know that it all get corrected here.
    req_cols = ['TOTALLOAD', 'WIND', 'SOLAR']
    final_dat = final_dat.loc(axis=0)['NY', 2050, :]
    final_dat = final_dat.join(df)[req_cols]
    final_dat = final_dat.reset_index(level=['HOUR'])
    final_dat = final_dat.reset_index(drop=True)
    print(final_dat)

    # Note -- While we are only outputting one data file, our "pointer"
    # csv file will list this file twice but with different years. This
    # allows us to interpolate for all the years of the project. So, for example
    # the Data.csv file will look something like:
    # scaling  YEAR  filename
    # 1        2020  Data_0.csv
    # 1        2050  Data_0.csv
    output_path = TRAIN_DIR.joinpath(case, "Output", "Data_0.csv")
    final_dat.to_csv(output_path, index=False)

if __name__ == '__main__':
    main()
