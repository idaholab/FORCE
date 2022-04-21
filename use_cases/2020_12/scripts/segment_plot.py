#!/usr/bin/env python3
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import product
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.arima_process import arma_generate_sample
from rom_plots import detrend
import warnings


BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath('train')

def load_data(file_path, segments):
    df = pd.read_csv(file_path)
    year = pd.unique(df.YEAR)[0]
    df = df.assign(
        TIMESTAMP = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(df.HOUR, unit="H"),
        SEGMENT = lambda x: pd.cut(x.HOUR, segments, labels=False)
    )
    return df


def plot_ac(df, fig, gs, **kwargs) -> None:
    """
    Plot Autocorrelation Data.

    @In: ax, plt.Axes, current axes to plot data with
    @In: _, pd.DataFrame, ARMA output unneeded for this plot
    @In: epri_dat, pd.DataFrame, Original EPRI data for specified year
    @Out: None
    """
    gs0 = gs.subgridspec(2, 1)
    ax0 = fig.add_subplot(gs0[0, :])
    ax1 = fig.add_subplot(gs0[1, :])
    values = df.RESIDUAL.to_numpy()
    sm.graphics.tsa.plot_acf(values, lags=40, ax=ax0)
    sm.graphics.tsa.plot_pacf(values, lags=40, ax=ax1)


def segment_plot(df):
    global_bases = [8760, 4380, 2190, 1251.42, 973, 515.29411, 438, 172, 168, 33.6, 23.93442623, 12, 8, 6]
    local_bases = [172, 168, 34, 24, 12, 8, 6]
    df = df.assign(
        FOURIER=lambda x: detrend(x.HOUR.to_numpy(), x.TOTALLOAD.to_numpy(), global_bases),
        RESIDUAL=lambda x: x.TOTALLOAD - x.FOURIER
    )

    # Plot of Fourier Decomposition
    fig = plt.figure(figsize=(30, 90))
    gs = fig.add_gridspec(nrows=72, ncols=7)
    gax = fig.add_subplot(gs[0:8, :])
    gax.plot(df.HOUR, df.TOTALLOAD, color="darkred")
    gax.plot(df.HOUR, df.FOURIER, '-', color="grey")
    gax.plot(df.HOUR, df.RESIDUAL, color="gold")
    gax.set_title("Fourier Detrend")

    # Plot of GlobalROM ARMA
    plot_ac(df, fig, gs[9:18, :])

    # # Plot each Segment ROM
    # gs_grid = list(product(range(19, 72), range(7)))
    # for (i, j), (k, d) in zip(gs_grid, df.groupby("SEGMENT")):
    #     ax = fig.add_subplot(gs[i, j])
    #     d = d.assign(
    #         ORIGINAL = d.TOTALLOAD,
    #         FOURIER=lambda x: detrend(x, local_bases),
    #         TOTALLOAD=lambda x: x.TOTALLOAD - x.FOURIER
    #     )
    #     # print(d)
    #     ax.plot(d.HOUR, d.ORIGINAL, color="red")
    #     # ax.plot(d.HOUR, d.FOURIER, color="grey")
    #     # ax.plot(d.HOUR, d.TOTALLOAD, color="gold")
    #     ax.set_title(f"Segment {k} Fit")

    fig.tight_layout()
    fig.savefig("grid_plot.png")

def main():
    file_path = TRAIN_DIR.joinpath("carbontax", "IL", "Data_3.csv")
    df = load_data(file_path, 365)
    df = df[["STATE", "YEAR", "HOUR", "TOTALLOAD", "SEGMENT"]]
    segment_plot(df)

if __name__ == '__main__':
    main()
