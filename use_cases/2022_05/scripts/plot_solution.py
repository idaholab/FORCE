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
import matplotlib.ticker as tic

# Global Constants
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath("train")
UNITS = ["$kW_{e}$", "$kWh_{e}$", "$kg-H_{2}$", "$kg-CO_{2}$", "$kg-H_{2}$", r"\$ (USD, 2020)"]
COLORS = ["darkgreen", "firebrick", "steelblue"]
CASEMAP = {
    'grid_sellall_kgh_test':'Test, high electricity prices',
    'grid_sellnothing_kgh_test':'Test, null electricity prices',
    'full_varpriceelec':"PJM ARMA based\n varying electricity prices"
}

# Plot Settings
plt.rc("figure", figsize=(7, 10))
plt.rc("axes", labelsize=12, titleweight="bold", axisbelow=True, grid=True)
plt.rc("legend", fontsize=12)
plt.rc("savefig", bbox="tight")
plt.rc(["xtick", "ytick"], labelsize=12)


def plot_optimizer(df, var_cols, args) -> None:

    # Data needed for plots
    dfa = df.query("accepted in ['first', 'accepted']")
    dfr = df.query("accepted not in ['first', 'accepted']")

    #last_dnpv = dfa['mean_NPV'].iloc[-1].squeeze() - baseline_mean_npv

    # Info needed for plots
    colors = {v: c for v, c in zip(["accepted", "rejected", "rerun"], COLORS)}
    units = {v: u for v, u in zip(var_cols, UNITS)}

    # Drop NPP_bid_adjust if in Regulated
    var_cols = [v for v in var_cols if v in df.columns.values]
    last_dat = {'case': CASEMAP[args.path.resolve().parent.name]}

    # Loop through the var_cols and plot each variable
    fig, axes = plt.subplots(nrows=len(var_cols), sharex=True)
    axes[-1].set_xlabel("Iteration")

    for var, ax in zip(var_cols, axes):
        # Sci. notation for everything > 100.
        # ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 2))
        # Title Case Vars, but don't change abbreviations...
        title = " ".join([i if i.isupper() else i.title() for i in var.split("_")])
        ax.set_title(title)
        ax.set_ylabel(units[var])

        #scalar = 0
        #if var == 'mean_NPV':
         #   ax.set_title("Mean NPV Relative to Baseline NPV")
          #  scalar = baseline_mean_npv

        for k, d in dfr.groupby("accepted"):
            y = np.abs(d[var].to_numpy()) 
            #if var == 'mean_NPV':
            #    y = d[var].to_numpy() - scalar
            ax.scatter(
                d.iteration.to_numpy(),
                y,
                c=d.accepted.map(colors),
                label=k,
                marker="o",
                alpha=0.8,
            )
        y = np.abs(dfa[var].to_numpy()) 
        if var == 'mean_NPV':
            y = dfa[var].to_numpy() 
        ax.plot(
            dfa.iteration.to_numpy(),
            y,
            label="accepted",
            color=colors["accepted"],
            marker="o",
            linestyle="-",
        )
        last_dat[var] = dfa[var].iloc[-1].squeeze()
        if 'storage' in var:
            yabs_max = abs(max(ax.get_ylim(), key=abs)) + 0.10
            ax.set_ylim(bottom=-0.10, top=yabs_max)
            formatter = tic.StrMethodFormatter('{x:.2f}')
            ax.yaxis.set_major_formatter(formatter)




    print(f"{'Mean NPV:':<20} {last_dat['mean_NPV']/1e6:>10.2f} (M$ USD)")
    #print(f"{'Delta NPV:':<20} {last_dnpv/1e6:>10.2f}")
    last_dat['mean_NPV'] = last_dat['mean_NPV'] / 1e6
    #last_dat['baseline_NPV'] = baseline_mean_npv / 1e6
    #last_dat['dNPV'] = last_dnpv / 1e6
    #last_dat['Change'] = (last_dat['mean_NPV'] - last_dat['baseline_NPV']) / last_dat['baseline_NPV']
    last_dat_df = pd.DataFrame(last_dat, index=[0])
    last_dat_df = last_dat_df.rename(
        columns={
            'mean_NPV': 'Mean NPV (M $USD)',
            #'baseline_NPV': 'Baseline NPV',
            #'dNPV': 'Δ NPV',
            'h2_storage_capacity': 'H2 Storage, (kg)',
            'CO2_source_capacity': 'CO2 Source, (kg/h)',
            'ft_capacity': r'FT (Fischer-Tropsch), (kg-H_{2})',
            'htse_capacity': 'HTSE (kWe)',
            'turbine_capacity': 'Turbine (kWe)',
            'case': 'Case'
        }
    )
    last_dat_df.to_csv(args.path.resolve().parent/'final_iter.csv', index=False)
    # Set middle axes to have legend to the right of the plot.
    # Also reorder legend to have 'accepted' appear on top.
    handles, labels = axes[-1].get_legend_handles_labels()
    labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
    # Add Case Title
    casetype = CASEMAP[args.path.resolve().parent.name]
    lg = fig.legend(
        handles,
        labels,
        markerscale=1.2,
        bbox_to_anchor=(1, 0.5),
        title=casetype,
    )
    plt.setp(lg.get_title(), multialignment="center")
    fig.tight_layout()
    # Have to update canvas to get actual legend width
    fig.canvas.draw()
    # The following will place the legend in a non-weird place
    frame_w = lg.get_frame().get_width()
    fig.subplots_adjust(right=get_adjust(lg.get_frame().get_width()))



def get_adjust(width):
    if width < 149:
        return 0.78
    elif width < 164:
        return 0.73
    elif width < 169:
        return 0.73
    else:
        return 0.7


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="Path to solution output csv.")
    args = parser.parse_args()

    df = pd.read_csv(args.path)
    var_cols = [
        "turbine_capacity",
        "htse_capacity",
        "ft_capacity",
        "CO2_source_capacity",
        "h2_storage_capacity",
        "mean_NPV",
    ]

    plot_optimizer(df, var_cols, args)
    plt.savefig(args.path.resolve().parent/"solution.png")


if __name__ == "__main__":
    main()
