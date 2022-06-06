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
from matplotlib.ticker import MaxNLocator

# Global Constants
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath("train")
COLORS = ["darkgreen", "firebrick", "steelblue"]
CASEMAP = {'LWR': 'AP1000, 1117 MWe', 
          'SMR': 'NuScale, 77 MWe', 
          'micro_HOLOS': 'HOLOS, Titan, 81 MWe'
}
CAPACITIES = {
  'LWR': 1117, 
  'SMR': 77, 
  'micro_HOLOS': 81
}
UNITS = {
  "turbine_capacity": "$MW_{e}$",
  "htse_capacity": "$MW_{e}$",
  "ft_capacity": "$kg-H_{2}$",
  "h2_storage_capacity": "$kg-H_{2}$",
  "mean_NPV": r"\$ (USD, 2020)",
  'Change': "%", 
  "dNPV": r"\$ (USD, 2020)"
}


# Plot Settings
plt.rc("figure", figsize=(7, 10))
plt.rc("axes", labelsize=12, titleweight="bold", axisbelow=True, grid=True)
plt.rc("legend", fontsize=12)
plt.rc("savefig", bbox="tight")
plt.rc(["xtick", "ytick"], labelsize=12)


def plot_optimizer(case_name, df, var_cols, baseline_mean_npv) -> None:
  """
  Plot the optimization path and create a csv file with the final optimization results
    @ In, case_name, str, name of the case, must be in the CASEMAP keys
    @ In, df, pandas.DataFrame, dataframe with the case's optimization data
    @ In, var_cols, list[string], names for the optimization variables for the plot
    @ In, baseline_mean_npv, float, value of the baseline mean NPV to compare the case to
    @ Out, None
  """
  # Data needed for plots
  dfa = df.query("accepted in ['first', 'accepted']")
  dfr = df.query("accepted not in ['first', 'accepted']")

  last_dnpv = dfa['mean_NPV'].iloc[-1].squeeze() - baseline_mean_npv

  # Info needed for plots
  colors = {v: c for v, c in zip(["accepted", "rejected", "rerun"], COLORS)}

  var_cols = [v for v in var_cols if v in df.columns.values]
  casetype = CASEMAP[case_name]

  # Loop through the var_cols and plot each variable
  fig, axes = plt.subplots(nrows=len(var_cols), sharex=True)
  axes[-1].set_xlabel("Iteration")

  # Create dict for final result of optimization
  last_dat ={'description': casetype}
  #last_dat = {'case': casetype}

  for var, ax in zip(var_cols, axes):
      # Sci. notation for everything > 100.
      ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 2))
      # Title Case Vars, but don't change abbreviations...
      title = " ".join([i if i.isupper() else i.title() for i in var.split("_")])
      ax.set_title(title)
      try: 
        ax.set_ylabel(UNITS[var])
      except KeyError as e: 
        print(f"Capacity unit has not been specified in the UNITS map: {e}")

      # Only integer values for x axis
      ax.xaxis.set_major_locator(MaxNLocator(integer=True))

      if var == 'mean_NPV':
        ax.set_title(r"$\Delta$ Mean NPV")

      for k, d in dfr.groupby("accepted"):
          y = np.abs(d[var].to_numpy()) 
          # Compute delta mean NPV
          if var == 'mean_NPV':
              y = d[var].to_numpy() - baseline_mean_npv
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
  # Set middle axes to have legend to the right of the plot.
  # Also reorder legend to have 'accepted' appear on top.
  handles, labels = axes[-1].get_legend_handles_labels()
  labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0]))
  # Add Case Title
  lg = fig.legend(
      handles,
      labels,
      markerscale=1.2,
      bbox_to_anchor=(1.05, 0.5),
      title=casetype,
  )
  plt.setp(lg.get_title(), multialignment="center")
  fig.tight_layout()
  # Have to update canvas to get actual legend width
  fig.canvas.draw()
  # The following will place the legend in a non-weird place
  fig.subplots_adjust(right=get_adjust(lg.get_frame().get_width()))

  # Add values to final optimization result dictionary
  last_dat['baseline_NPV'] = baseline_mean_npv /1e6
  last_dat['mean_NPV'] = last_dat['mean_NPV'] / 1e6
  last_dat['dNPV'] = last_dnpv / 1e6
  last_dat['Change'] = (last_dat['mean_NPV'] - last_dat['baseline_NPV']) / last_dat['baseline_NPV']

  return last_dat
  
  



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

    # Get the baseline mean NPV
    baseline_path = args.path.resolve().parent.parent.parent / 'baseline' / 'gold' / 'sweep.csv'
    baseline_df = pd.read_csv(baseline_path)
    case_name = args.path.resolve().parent.parent.name
    capacity = CAPACITIES[case_name]
    baseline_df = baseline_df.query(f'turbine_capacity == {capacity}')
    baseline_mean_npv = (baseline_df[['mean_NPV']].squeeze())

    # Case plot
    df = pd.read_csv(args.path)
    var_cols = UNITS.keys()

    # Retrieve final results of optimization
    opt_res = plot_optimizer(case_name, df, var_cols, baseline_mean_npv)
    plt.savefig(args.path.resolve().parent.parent/"solution.png")

    # Save final optimization results
    # Check if all cases file has been created
    final = args.path.resolve().parent.parent.parent / 'final_opt.csv'
    if final.exists(): 
      final_df = pd.read_csv(final)
    else: 
      final_df = pd.DataFrame(columns =['Case', 'description']+list(UNITS.keys()))
      final_df['Case'] = CASEMAP.keys()
      final_df.set_index('Case', inplace=True)
    for k,v in opt_res.items(): 
      final_df.loc[case_name, k] = v
    '''last_dat_df = last_dat_df.rename(
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
    )'''
    final_df.to_csv(final, index=True)


if __name__ == "__main__":
    main()
