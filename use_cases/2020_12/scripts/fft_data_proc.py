#!/usr/bin/env python3
"""Plot FFT Results for EPRI Cases."""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.font_manager import FontProperties


# Global Constants
YEARS = np.arange(2025, 2055, 5)
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath("train")

# Matplotlib Global Settings
mpl.rc("figure", figsize=(25, 10))
mpl.rcParams["figure.constrained_layout.use"] = True
mpl.rc(
    "axes",
    titlesize=18,
    titleweight="bold",
    labelsize=18,
    axisbelow=True,
    grid=True
)
mpl.rc("savefig", bbox="tight")
mpl.rc("legend", fontsize="large")
mpl.rc(["xtick", "ytick"], labelsize=15)


def read_assign(file_path: Path) -> pd.DataFrame:
    """
    Annotate dataframe with identifying column on read-in.

    @In: file_path, Path, a Path to a csv-file.
    @Out: pd.DataFrame, an annotated dataframe of csv file.
    """
    basename = file_path.stem
    df = (
        pd.read_csv(file_path)
        .replace([np.inf, -np.inf], np.nan)  # Get rid of the inf period.
        .dropna()
        .assign(
            case=basename,
            TOTALLOAD_fft_amplitude = lambda x: np.abs(x.TOTALLOAD_fft_amplitude)
        )
    )
    threshold = 0.15 * np.max(np.abs(df.TOTALLOAD_fft_amplitude.to_numpy()))
    df = df[df.TOTALLOAD_fft_amplitude > threshold]
    df = df.assign(WHOLE = lambda x: x.TOTALLOAD_fft_period.apply(lambda y: int(y)))
    df = df.groupby("WHOLE").max()
    return df


def generate_plot(df: pd.DataFrame, args: argparse.Namespace) -> None:
    """
    Create plot containing FFT scatter plot and table.

    @In: df, pd.DataFrame, a dataframe for plotting data.
    @In: args, NameSpace, a container for script arguments.
    @Out: None
    """
    fig = plt.figure()
    gs = fig.add_gridspec(3, 1)
    generate_scatter(df, fig, gs, args)
    generate_table(df, fig, gs, args)
    fig.savefig(f"fft_{args.state.lower()}_results.png")


def generate_scatter(df: pd.DataFrame,
                     fig: plt.Figure,
                     gs: plt.GridSpec,
                     args: argparse.Namespace) -> None:
    """
    Add scatter plot of fft results to figure.

    @In: df, pd.DataFrame, dataframe to plot.
    @In: fig, plt.Figure, figure containing plot.
    @In: gs, plt.GridSpec, grid-layout for multiple plots.
    @In: args, Namespace, container holding script args.
    @Out: None
    """
    ax = fig.add_subplot(gs[0:-1, :])
    for (key, dat) in df.groupby(["case"]):
        ax.plot(
            dat.TOTALLOAD_fft_period, dat.TOTALLOAD_fft_amplitude, "o",
            label=key, alpha=0.5, markersize=12, markeredgecolor="k"
        )
    ax.set_xlabel("Period (Hour)")
    ax.set_ylabel("Magnitude")
    ax.legend([f"FFT {i}" for i in YEARS])
    ax.set_title(f"{args.state} Total Load FFT Results")


def generate_table(df: pd.DataFrame,
                   fig: plt.Figure,
                   gs: plt.GridSpec,
                   args: argparse.Namespace) -> None:
    """
    Add significant integer periods as table to figure.

    @In: df, pd.DataFrame, dataframe to plot.
    @In: fig, plt.Figure, figure containing plot.
    @In: gs, plt.GridSpec, grid-layout for multiple plots.
    @In: args, Namespace, container holding script args.
    @Out: None
    """
    # Find all whole-numbers that have amplitude > 0.1 in df.
    # Place this table below the plot
    ax = fig.add_subplot(gs[-1, :])
    ## Pivot the dataframe so periods are column-names.
    ## aggfunc='mean' effectively does nothing here since
    ## There should only be one observation of a period per year.
    tb = pd.crosstab(
        df.case,
        df.TOTALLOAD_fft_period, values=df.TOTALLOAD_fft_amplitude,
        aggfunc='mean'
    )
    # Make row-names human readable
    tb = tb.rename(index={f"fft_final_{i}": year for i, year in enumerate(YEARS)})
    tb = tb.transform(lambda x: round(x, 5))
    tb.write_csv('fft_table.csv')
    table = pd.plotting.table(ax, tb, bbox=[0, 0, 1, 1])
    # Make headers and row-names bold.
    for (row, col), cell in table.get_celld().items():
        if (row == 0) or (col == -1):
            cell.set_text_props(fontproperties=FontProperties(weight='bold'))
    ax.set_title(f"{args.state} Significant Normalized Amplitude (> 0.1)")
    ax.set_axis_off()
    table.set_fontsize(15)
    table.scale(2, 1)


def main():
    """Driver Function."""
    parser = argparse.ArgumentParser(
        description="FFT Plotting Script for EPRI Data"
    )
    parser.add_argument(
        "-s", "--state",
        type=str,
        default='IL',
        help="Specify which state data to visualize."
    )
    parser.add_argument(
        "-c", "--case",
        type=Path,
        default=Path.cwd().name,
        help="Specify which scenario data to visualize."
    )
    args = parser.parse_args()
    case_dir = TRAIN_DIR.joinpath(args.case)
    state_dir = case_dir.joinpath(args.state)
    fft_results = state_dir.glob("fft_final_*.csv")
    df = pd.concat([read_assign(fp) for fp in fft_results])
    tb = pd.crosstab(
        df.case,
        np.floor(df.TOTALLOAD_fft_period),
        values=df.TOTALLOAD_fft_amplitude,
        aggfunc='mean'
    )
    tb = tb.rename(index={f"fft_final_{i}": year for i, year in enumerate(YEARS)})
    tb.to_csv(Path("./", "test.csv"))



if __name__ == "__main__":
    main()
