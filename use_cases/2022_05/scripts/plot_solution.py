#!/usr/bin/env python3
"""Plot Solutions to HERON Runs"""
# Internal Libs
import argparse
from email.mime import base
from pathlib import Path
from telnetlib import EL
from typing import List

# External Libs
import pandas as pd
import numpy as np
import matplotlib as mpl
mpl.use('Agg') # Prevents the script from blocking while plotting
import matplotlib.pyplot as plt
import matplotlib.ticker as tic
from matplotlib.ticker import MaxNLocator
import os

# Global Constants
BASE_DIR = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR.joinpath("train")
RUN_DIR = BASE_DIR.joinpath("run")
COLORS = ["darkgreen", "firebrick", "steelblue"]
CASEMAP = {'LWR_ref': 'LWR, reference fuel prices', 
          'LWR_low': 'LWR, low fuel prices',
          'LWR_high': 'LWR, high fuel prices',
}
BASELINE_MAP ={
  'LWR_ref': 'synfuel_baseline',
  'LWR_low': 'synfuel_baseline_low',
  'LWR_high': 'synfuel_baseline_high'
}
CAPACITIES = {
  'LWR_ref': 1000, 'LWR_low':1000, "LWR_high":1000, 
  'SMR': 300, 
  'micro': 50
}
ELEC_BASELINE = RUN_DIR.joinpath('baseline/gold/sweep_30y.csv')
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


def plot_optimizer(args, case_name, df, var_cols, baseline_mean_npv, baseline_case) -> None:
  """
  Plot the optimization path and create/fills out a csv file with the final optimization results
    @ In, args, str, path to output optimization file
    @ In, case_name, str, name of the case, must be in the CASEMAP keys
    @ In, df, pandas.DataFrame, dataframe with the case's optimization data
    @ In, var_cols, list[string], names for the optimization variables for the plot
    @ In, baseline_mean_npv, float, value of the baseline mean NPV to compare the case to
    @ In, baseline_case, string, name of the baseline case to compare the case to 
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
          y = dfa[var].to_numpy() - baseline_mean_npv
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
  name_fig = "solution_"+case_name+"_"+baseline_case+"_baseline.png"
  plt.savefig(args.path.resolve().parent.parent/name_fig)
  plt.close()
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

    # Get the baseline cases mean NPV
    case_name = args.path.resolve().parent.parent.name
    syn_fuel_path = RUN_DIR.joinpath(BASELINE_MAP[case_name]).joinpath('gold/sweep_30y.csv')
    elec_baseline_df = pd.read_csv(ELEC_BASELINE)
    syn_baseline_df = pd.read_csv(syn_fuel_path)
    
    capacity = CAPACITIES[case_name]
    print(f"Case being post-processed : {case_name} ({capacity} MWe)")
    elec_baseline_df = elec_baseline_df.query(f'turbine_capacity == {capacity}')
    elec_baseline_mean_npv = (elec_baseline_df[['mean_NPV']].squeeze())
    syn_baseline_df = syn_baseline_df.query(f'turbine_capacity == {capacity}')
    syn_baseline_mean_npv = (syn_baseline_df[['mean_NPV']].squeeze())

    # Case plot
    df = pd.read_csv(args.path)
    var_cols = UNITS.keys()

    # Retrieve final results of optimization
    elec_opt_res = plot_optimizer(args, case_name, df, var_cols, elec_baseline_mean_npv, 'electricity')
    # TODO plot results for corresponding synfuel baseline too and save fig
    syn_opt_res = plot_optimizer(args, case_name, df, var_cols, syn_baseline_mean_npv, BASELINE_MAP[case_name])

    # Save final optimization results
    # Check if all cases file has been created
    # Final optimization results compared to electricity baseline
    final_elec = args.path.resolve().parent.parent.parent / 'final_elec_opt.csv'
    final_syn = args.path.resolve().parent.parent.parent / 'final_synfuel_baseline_opt.csv'
    save_final(case_name=case_name, final_path=final_elec, opt_res=elec_opt_res, baseline_name='elec')
    save_final(case_name=case_name, final_path=final_syn, opt_res=syn_opt_res, baseline_name=BASELINE_MAP[case_name])
    
def save_final(case_name, final_path, opt_res, baseline_name):
  """
  Save final optimization results
  Check if all cases file has been created 
  @ In, case_name, str, name of the case being saved
  @ In, final_path, str, path to final results compared to particular baseline
  @ In, opt_res, dict, results of optimization i.e. final components' capacities to
  @ In, baseline_name, str, name of the baseline used for the comparison
  @ Out, None
  """
  if os.path.exists(final_path): 
      final_df = pd.read_csv(final_path, index_col='Case')
      print('File already exists, here is the info in it')
      print('Baseline case: {}'.format(baseline_name))
      print(final_df)
      #os.remove(final_path)
  else: 
    final_df = pd.DataFrame(columns =['Case', 'description']+list(UNITS.keys()))
    final_df['Case'] = CASEMAP.keys()
    final_df.set_index('Case', inplace=True)
  for k,v in opt_res.items(): 
    final_df.loc[case_name, k] = v
  # If all cases have been written clean up columns names
  if not final_df.isnull().values.any(): 
    plot_final(final_df)
  with open(final_path, 'w') as final:
      final_df.to_csv(final, index=True, line_terminator='\n')


def plot_final(df): 
  """
  Save the complete data from all cases and creates a bar plot to show final components' capacities
  @ In, df, pandas.DataFrame, dataframe with data for each case
  @ Out, None
  """
  columns={
            'mean_NPV': 'Mean NPV (M $USD(2020))',
            'description': 'Description',
            'baseline_NPV': 'Baseline NPV (M $USD(2020))',
            'dNPV': 'Delta NPV (M $USD(2020))',
            'h2_storage_capacity': 'H2 Storage, (kg)',
            'ft_capacity': 'FT (Fischer-Tropsch), (kg-H2)',
            'htse_capacity': 'HTSE (MWe)',
            'turbine_capacity': 'Turbine (MWe)', 
            'Change': 'Change (%)'
        }
  mpl.style.use('fivethirtyeight')
  fig, axes = plt.subplots(ncols=2)
  ax = axes[0]
  ax.set_title("Optimized components capacities")
  df_plot = df[['description', 'h2_storage_capacity', 'ft_capacity', 'htse_capacity', 'turbine_capacity']].copy()
  df_plot.rename(columns, inplace=True)
  df_plot.transpose()
  df_plot.plot(kind="bar", ax=ax, legend=True)
  ax = axes[1]
  ax.set_title("Net Present Value Comparison")
  df_plot = df[['baseline_NPV','mean_NPV', 'dNPV', 'Change']].copy()
  df_plot.rename(columns, inplace=True)
  df_plot.transpose()
  df_plot.plot(kind="bar", ax=ax).legend(loc='upper center', title="Cases")
  plt.savefig("final_cases.png")






if __name__ == "__main__":
    main()
