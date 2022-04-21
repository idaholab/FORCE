#!/usr/bin/env python3
"""Plot Solutions to HERON Runs"""
# Internal Libs
import argparse
from pathlib import Path
from typing import List

# External Libs
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # Prevents the script from blocking while plotting
import matplotlib.pyplot as plt

# Global Constants
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath("train")
UNITS = ["kg/s", "kg", "kg/s", "$/GW (USD)", r"$\Delta$\$ (USD)"]
COLORS = ["darkgreen", "firebrick", "steelblue"]

# Plot Settings
plt.rc("figure", figsize=(7, 10))
plt.rc("axes", labelsize=12, titleweight="bold", axisbelow=True, grid=True)
plt.rc("legend", fontsize=12)
plt.rc("savefig", bbox="tight")
plt.rc(["xtick", "ytick"], labelsize=12)


def plot_optimizer(df: pd.DataFrame, var_cols: List[str], args: argparse.Namespace) -> None:
    # Determine which prefix to use for results file
    if args.path.resolve().parent.parent.name == 'Deregulated':
        prefix = 'D_'
    else:
        prefix = 'R_'

    # Construct results path
    rpath = args.path.resolve().parent.parent/'results'
    results = rpath / f"{prefix}{'_'.join(args.path.parent.name.split('_')[1:])}_baseline.csv"

    # Data needed for plots
    mean_npv = pd.read_csv(results)[['mean_NPV']].squeeze()
    dfa = df.query("accepted in ['first', 'accepted']")
    last_dnpv = dfa['mean_NPV'].iloc[-1].squeeze() - mean_npv
    dfr = df.query("accepted not in ['first', 'accepted']")

    # Info needed for plots
    colors = {v: c for v, c in zip(["accepted", "rejected", "rerun"], COLORS)}
    units = {v: u for v, u in zip(var_cols, UNITS)}

    # Drop NPP_bid_adjust if in Regulated
    var_cols = [v for v in var_cols if v in df.columns.values]
    last_dat = {'case': args.path.parent.name}

    # Loop through the var_cols and plot each variable
    fig, axes = plt.subplots(nrows=len(var_cols), sharex=True)
    axes[-1].set_xlabel("Iteration")
    for var, ax in zip(var_cols, axes):
        # Sci. notation for everything > 100.
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 2))
        # Title Case Vars, but don't change abbreviations...
        title = " ".join([i if i.isupper() else i.title() for i in var.split("_")])
        ax.set_title(title)
        ax.set_ylabel(units[var])

        scalar = 0
        if var == 'mean_NPV':
            ax.set_title("Mean NPV Relative to Baseline NPV")
            scalar = mean_npv

        for k, d in dfr.groupby("accepted"):
            y = np.abs(d[var].to_numpy()) - scalar
            if var == 'mean_NPV':
                y = d[var].to_numpy() - scalar
            ax.scatter(
                d.iteration.to_numpy(),
                y,
                c=d.accepted.map(colors),
                label=k,
                marker="o",
                alpha=0.8,
            )
        y = np.abs(dfa[var].to_numpy()) - scalar
        if var == 'mean_NPV':
            y = dfa[var].to_numpy() - scalar
        ax.plot(
            dfa.iteration.to_numpy(),
            y,
            label="accepted",
            color=colors["accepted"],
            marker="o",
            linestyle="-",
        )
        last_dat[var] = dfa[var].iloc[-1].squeeze()

    last_dat['dNPV'] = last_dnpv
    last_dat_df = pd.DataFrame(last_dat, index=[0])
    last_dat_df.to_csv(args.path.parent.resolve()/'final_iter.csv')
    # Set middle axes to have legend to the right of the plot.
    # Also reorder legend to have 'accepted' appear on top.
    handles, labels = axes[-1].get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    # Add Case Title
    casetype = args.path.resolve().parent.parent.name
    figtitle = args.path.parent.name.replace("_", "\\_")
    lg = fig.legend(
        handles,
        labels,
        markerscale=1.2,
        bbox_to_anchor=(1, 0.5),
        title=f"$\\bf{{ {casetype} }}$\n$\\bf{{ {figtitle} }}$",
    )
    plt.setp(lg.get_title(), multialignment="center")
    fig.tight_layout()
    # Have to update canvas to get actual legend width
    fig.canvas.draw()
    # The following will place the legend in a non-weird place
    fig.subplots_adjust(right=get_adjust(lg.get_frame().get_width()))


def get_adjust(width):
    if width < 149:
        return 0.76
    elif width < 164:
        return 0.75
    elif width < 169:
        return 0.72
    else:
        return 0.7


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="Path to solution output csv.")
    args = parser.parse_args()

    df = pd.read_csv(args.path)
    try:
        df = df.assign(
            HTSE_capacity = lambda x: x.IES_delta_cap + (- x.H2_market_capacity)
        )
    except AttributeError as e:
        print(args.path)
        print(e)
    var_cols = [
        "HTSE_capacity",
        "H2_storage_capacity",
        "H2_market_capacity",
        "NPP_bid_adjust",
        "mean_NPV",
    ]

    plot_optimizer(df, var_cols, args)
    fig_dir = args.path.parent.resolve()
    plt.savefig(fig_dir / "solution.png")


if __name__ == "__main__":
    main()
