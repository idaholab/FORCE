#!/usr/bin/env python
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


YEARS = np.arange(2020, 2055, 5)
HOURS = np.arange(1, 8761, 1)

plt.rc("figure", figsize=(15, 10))
plt.rc(
    "axes",
    titlesize=20,
    titleweight="bold",
    labelsize=20,
    axisbelow=True,
    grid=True
)
plt.rc("savefig", bbox="tight")
plt.rc("legend", fontsize=20)
plt.rc(["xtick", "ytick"], labelsize=20)

def main():
    req_cols = ['RAVEN_sample_ID','YEAR','HOUR','TOTALLOAD','WIND','SOLAR']
    synth = (
        pd.read_csv(
            Path('./Output/synth.csv').resolve(),
            usecols=req_cols,
            index_col=req_cols[0:3],
        )
        .sort_index()
    )

    real = (
        pd.read_csv(
            Path('./Output/Data_0.csv').resolve(),
        )
        .sort_index()
    )

    print(real)

    dat = synth.loc(axis=0)[:, 2050, :]

    fig = plt.figure(tight_layout=True)
    ax0 = fig.add_subplot(131)
    ax1 = fig.add_subplot(132)
    ax2 = fig.add_subplot(133)

    for k, d in dat.groupby('RAVEN_sample_ID'):
        ax0.plot(HOURS, d['TOTALLOAD'], color='darkblue', alpha=0.2, label='Synthetic')
        ax1.plot(HOURS, d['WIND']*100, color='darkblue', alpha=0.2, label='Synthetic')
        ax2.plot(HOURS, d['SOLAR']*100, color='darkblue', alpha=0.2, label='Synthetic')

    ax0.plot(HOURS, real['TOTALLOAD'], color='darkred', label='US-REGEN')
    ax1.plot(HOURS, real['WIND']*100, color='darkred', label='US-REGEN')
    ax2.plot(HOURS, real['SOLAR']*100, color='darkred', label='US-REGEN')

    ax0.set_title("Load Demand (GW)")
    ax1.set_title("Wind Capacity Utilization")
    ax2.set_title("Solar Capacity Utilization")

    ax1.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

    h, l = ax0.get_legend_handles_labels()
    by_label = dict(zip(l, h))
    leg = ax0.legend(by_label.values(), by_label.keys(), loc='upper right')
    for lh in leg.legendHandles:
        lh.set_alpha(1)

    fig.supxlabel('Time (Hour)', fontsize=20)
    plt.savefig('synth_plot.png')




if __name__ == '__main__':
    main()
