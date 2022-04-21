from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from itertools import product
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.arima_process import arma_generate_sample
from rom_plots import detrend
import warnings


BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath('train')

mpl.rc("figure", figsize=(25, 10))
mpl.rc(
    "axes",
    titlesize=18,
    titleweight="bold",
    labelsize=25,
    axisbelow=True,
    grid=True
)
mpl.rc("savefig", bbox="tight")
mpl.rc("legend", fontsize=18)
mpl.rc(["xtick", "ytick"], labelsize=20)


def gauss_bandpass(fou, freq):
    """
    https://stackoverflow.com/questions/36968418/python-designing-a-time-series-filter-after-fourier-analysis
    """
    dof = 0.5
    f1, f2 = 8760, 4380
    gpl = np.exp(-((freq - f1)/(2 * dof))**2) + np.exp(-((freq - f2)/(2 * dof))**2)
    gmn = np.exp(-((freq + f1)/(2 * dof))**2) + np.exp(-((freq + f2)/(2 * dof))**2)
    g = gpl + gmn
    return fou * g


def ts_fft(df):
    load = (df.TOTALLOAD.to_numpy() - df.TOTALLOAD.to_numpy().mean())
    freq = np.fft.fftfreq(len(load))
    spectrum = np.fft.fft(load)
    threshold = 0.5 * np.max(np.abs(spectrum))
    masks = np.abs(spectrum) > threshold
    peaks = freq[masks]
    return peaks, spectrum[masks]


def spectrum_plot(freq, fou):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(np.fft.fftshift(freq), np.fft.fftshift(np.abs(fou)))
    plt.show()

def load_data(file_path):
    df = pd.read_csv(file_path)
    df = df.assign(LABEL=file_path.name)
    return df


def main():
    data_dir = TRAIN_DIR/"carbontax_lnhr"/"IL"
    df = pd.concat([load_data(fp) for fp in data_dir.glob("fft_final_*.csv")])
    year = 2025

    fig = plt.figure(constrained_layout=True)
    ax = fig.add_subplot(111)
    for key, dat in df.groupby("LABEL"):
        ax.semilogx(dat.iloc[:,1], np.abs(dat.iloc[:,2]/8760), label=f"US-REGEN {year}")
        year += 5

    ax.set_xticks([10, 100, 1000, 10000])
    ax.set_xticklabels(["10", "100", "1000", "10000"])
    ax.set_ylabel("Normalized Magnitude")
    ax.set_xlabel("Period (Hour)")
    ax.legend()
    fig.savefig(TRAIN_DIR/"carbontax_lnhr"/"fft_analysis.png")


if __name__ == '__main__':
    main()
