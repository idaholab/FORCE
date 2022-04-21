#!/usr/bin/env python3
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter # type:ignore

# Matplotlib Global Settings
plt.rc("figure", figsize=(12, 8), titleweight='bold')
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

def electro(df, ax):
    var_cols = [
        'Dispatch__HTSE__electricity',
        'Dispatch__grid__electricity',
        'Dispatch__Coal__electricity',
        'Dispatch__Gas__electricity',
        'Dispatch__Petrol__electricity',
        'Dispatch__H2gen__electricity',
        'Dispatch__Nuclear__electricity',
        'Dispatch__VRE__electricity',
        'Dispatch__Other__electricity',
    ]
    labels = ["NPP power to HTSE", "NPP power to Grid", "Coal", "Gas", "Petrol", "H2gen", "Nuclear", "VRE", "Other"]
    colors = ['tab:olive', 'tab:grey', "navy", "orangered", "black", "aqua", "chartreuse", "violet", "sienna"]
    ax.set_ylabel("Electricity (GW)")
    for var, lab, col in zip(var_cols, labels, colors):
        ax.plot(
            df.reset_index()['HOUR'], np.abs(df[var]), '-o',
            label=lab, color=col
        )
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.01f}"))


def dump(df, ax):
    var_cols = [
        # 'Dispatch__E_Penalty__electricity',
        'Dispatch__Secondary__electricity',
    ]
    labels = ['Overproduction Penalty', 'Underproduction Penalty']
    colors = ['tab:cyan', 'tab:purple']
    ax.set_ylabel("Expense ($ USD)")

    for var, lab, col in zip(var_cols, labels, colors):
        ax.plot(
            df.reset_index()['HOUR'], np.abs(df[var]), '-o',
            label=lab, color=col
        )
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))



def hydro(df, ax):
    df = df.assign(
        storage_prod = lambda x: np.diff(x['Dispatch__H2_storage__H2'], prepend=[0]) / 3600 * -1
    )
    var_cols = [
        'Dispatch__HTSE__H2',
        'Dispatch__H2_market__H2',
        'storage_prod'
    ]
    labels = ['HTSE H2', 'H2 Market', 'H2 Storage Production']
    colors = ['tab:blue', 'tab:green', 'tab:red']
    ax.set_ylabel("Hydrogen (kg/sec)")
    for var, lab, col in zip(var_cols, labels, colors):
        y = np.abs(df[var])
        if var == 'storage_prod':
            y = df[var]
        ax.plot(
            df.reset_index()['HOUR'], y, '-o',
            label=lab, color=col
        )
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.02f}"))


def storage(df, ax):
    var_cols = [
        'Dispatch__H2_storage__H2',
        'TOTALLOAD'
    ]
    df['Dispatch__H2_storage__H2'] = df['Dispatch__H2_storage__H2'].apply(lambda x: x if x > 0 else round(x))
    ax1 = ax
    ax1.set_ylabel('Storage (MW)')
    ax1.plot(
        df.reset_index()['HOUR'], df[var_cols[0]], '-o',
        label='H2 Storage', color='tab:red'
    )
    ax.tick_params(axis='y', labelcolor='tab:red')
    ax2 = ax1.twinx()
    ax2.set_ylabel('Load (GW)')
    ax2.plot(
        df.reset_index()['HOUR'], df[var_cols[1]], '-o',
        label='Market Load', color='tab:grey'
    )
    ax2.tick_params(axis='y', labelcolor='tab:grey')
    h1, l1, h2, l2 = ax1.get_legend_handles_labels() + ax2.get_legend_handles_labels()
    handles, labels = (h1 + h2, l1 + l2)
    ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1.1, 0.5))
    ax1.set_yticks(np.linspace(ax1.get_ybound()[0], ax1.get_ybound()[1], 4))
    ax2.set_yticks(np.linspace(ax2.get_ybound()[0], ax2.get_ybound()[1], 4))


def load_data(file_path):
    df = (
        pd.read_csv(file_path)
        .sort_values(['RAVEN_sample_ID', 'YEAR', '_ROM_Cluster', 'HOUR'])
    )
    df = df.set_index([
        'RAVEN_sample_ID',
        'YEAR',
        '_ROM_Cluster',
        'HOUR'
    ])
    df = df.drop([
        'strategy_label',
        'price_struct_label',
        'state_label',
        'prefix',
        'scaling',
        'PointProbability',
        'ProbabilityWeight',
        # 'E_Penalty_capacity',
    ], axis=1)
    return df


def main():
    results_dir = Path.cwd()
    dispatch_csv = results_dir.joinpath("dispatch_out_file.csv")

    idx = pd.IndexSlice
    df = load_data(dispatch_csv)
    df = df.loc[idx[0, 2025, 0, :]]

    fig, axes = plt.subplots(nrows=3, sharex=True)

    for ax in axes:
        ax.set_xticks(np.arange(0, 25, 2))
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 2))
    axes[-1].set_xlabel("Time (h)")

    electro(df, axes[0])
    # dump(df, axes[1])
    hydro(df, axes[1])
    storage(df, axes[2])
    fig.suptitle('Regulated Market Dispatch')
    fig.tight_layout()
    fig.savefig('../../../../dispatch.png')



if __name__ == '__main__':
    main()
