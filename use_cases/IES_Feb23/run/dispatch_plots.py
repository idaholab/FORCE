#!/usr/bin/env python3
from pathlib import Path
import sys, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter # type:ignore

# Matplotlib Global Settings
plt.rc("figure", figsize=(25,15), titleweight='bold')
plt.rc(
    "axes",
#     titlesize=25,
    titleweight="bold",
    labelsize=12,
    axisbelow=True,
    grid=True
)
plt.rc("savefig", bbox="tight")
plt.rc("legend", fontsize=12)
plt.rc(["xtick", "ytick"], labelsize=10)

def hydrogen(df, ax):
  var_cols_1 = [
        'Dispatch__htse__production__h2',
        'Dispatch__h2_storage__charge__h2', 
        'Dispatch__h2_storage__discharge__h2',
        'Dispatch__ft__production__h2'
  ]
  var_cols_2 =[
        'Dispatch__h2_storage__level__h2'
  ]
  ax1 = ax
  ax1.set_ylabel('Hydrogen Rate (ton/hour)')
  labels1 = ["HTSE Production","H2 storage charge", "H2 storage discharge", "FT Consumption"]
  labels2 = ["H2 storage level"] 
  colors1 = ["aqua","violet", "black","orangered"]
  colors2 = ["chartreuse"]
  for var, lab, col in zip(var_cols_1, labels1, colors1):
      df[var] = abs(df[var])/1e3
      df.plot(x='hour', y=var,ax=ax1,marker='+',label=lab, color=col)
  ax1.yaxis.set_major_formatter(StrMethodFormatter("{x:,.01f}"))
  ax2 = ax1.twinx()
  ax2.set_ylabel("Hydrogen (ton)")
  for var, lab, col in zip(var_cols_2,labels2, colors2) :
    df[var] = df[var]/1e3
    df.plot(x='hour', y=var, ax=ax2,marker='.',label=lab,color=col)
  ax2.tick_params(axis='y', labelcolor='chartreuse')
  h1, l1, h2, l2 = ax1.get_legend_handles_labels() + ax2.get_legend_handles_labels()
  ax2.grid(False)
  ax.legend(h1, l1, loc='upper left')
  ax2.legend(h2, l2, loc='upper right')


def electricity(df, ax):
  var_cols_1 = [
        'Dispatch__npp__production__electricity',
        'Dispatch__htse__production__electricity',
        'Dispatch__electricity_market__production__electricity'
  ]
  ax.set_ylabel('Electricity (MW)')
  labels = ["NPP Production", "HTSE Consumption", "Grid Consumption"]
  for v in var_cols_1:
    df[v] = abs(df[v])
  colors = ['tab:green', 'tab:grey', "navy"]
  for var, lab, col in zip(var_cols_1, labels, colors):
    df.plot(x='hour',y=var,ax=ax,marker='+',linestyle='dashed',label=lab, color=col)
  ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.01f}"))
  ax2 = ax.twinx()
  ax2.set_ylabel('Price ($/MWh)')
  df.plot(x='hour', y='price', ax=ax2, marker=".",label='Price ($/MWh)', color='tab:red')
  ax2.tick_params(axis='y', labelcolor='tab:red')
  ax2.grid(False)
  h1, l1, h2, l2 = ax.get_legend_handles_labels() + ax2.get_legend_handles_labels()
  ax.legend(h1, l1, loc='upper left')
  ax2.legend(h2, l2, loc='upper right')

def synfuels(df, ax):
  var_cols = [
        'Dispatch__ft__production__diesel',
        'Dispatch__ft__production__naphtha',
        'Dispatch__ft__production__jet_fuel'
  ]
  ax.set_ylabel('Synfuel (kg/h)')
  labels = ["Diesel", "Naphtha", "Jet Fuel"]
  colors = ['tab:green', 'tab:orange', "black"]
  for var, lab, col in zip(var_cols, labels, colors):
    df[var] = abs(df[var])
    df.plot(x='hour',y=var,ax=ax,marker='.',label=lab, color=col)
  h1, l1= ax.get_legend_handles_labels()
  ax.legend(h1, l1, loc='upper left')


def load_data(file_path):
    df = (
        pd.read_csv(file_path)
        .sort_values(['RAVEN_sample_ID', 'Year', '_ROM_Cluster', 'hour'])
    )
    #df = df.set_index(['_ROM_Cluster','hour'])
    df = df.drop([
        'Year',
        'RAVEN_sample_ID',
        'prefix',
        'scaling',
        'PointProbability',
        'ProbabilityWeight',
    ], axis=1)
    return df


def main(path):
    results_dir = os.path.dirname(path)
    # Load csv data into dataframe, select only first ROM cluster
    df = load_data(path)
    clusters = [i for i in range(20)] #20 later
    for cluster in clusters:
      temp_df = df.copy()
      temp_df = temp_df.loc[temp_df['_ROM_Cluster']==cluster]
      temp_df.set_index('hour')

      fig, axes = plt.subplots(nrows=3, sharex=True)

      for ax in axes:
          ax.set_xticks(np.arange(0, 121, 24))
          ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 2))
      axes[-1].set_xlabel("Time (h)")

      # plot dispatch for different resources on separate subplots
      electricity(temp_df, axes[0])
      hydrogen(temp_df, axes[1])
      synfuels(df, axes[2])
      fig.tight_layout()
      fig.savefig(os.path.join('../',results_dir,'dispatch_'+str(cluster)+'.png'))



if __name__ == '__main__':
  # User should pass the path to the dispatch file as argument when running this script
  if len(sys.argv) <2:
    print("Pass path to dispatch csv results file")
    exit()
  else:
    path = os.path.abspath(sys.argv[1])
    main(path)