#!/usr/bin/env python
"""
"""
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt # type: ignore
import matplotlib.ticker as ticker # type: ignore

plt.rc("figure", figsize=(15, 10))
plt.rc(
    "axes",
    titlesize=15,
    titleweight="bold",
    labelsize=12,
    labelweight='bold',
    axisbelow=True,
    grid=True
)
plt.rc("savefig", bbox="tight")
plt.rc(["xtick", "ytick"], labelsize=14)

REF_ARMA = pd.read_csv(Path('../train/ny_default_load/Output/synth.csv').resolve())
CES_ARMA = pd.read_csv(Path('../train/ny_ces_load/Output/synth.csv').resolve())


CASE_DICT = {('Reference', 'No_Storage'): {'coeffs': (12.791, 0.025),
                                           'windcap': 10.435570,
                                           'solarcap': 14.894274,
                                           'nucap': 1.143500,
                                           'x': [0.0, 4.277016, 5.420516, 9.953896, 27.178304, 62.178304],
                                           'y': [0.0, 0.000000, 12.689066, 25.109150, 32.703513, 169.679554],
                                           'arma': REF_ARMA
                                           },
              ('Reference', 'Storage'):    {'coeffs': (12.881, 0.026),
                                            'windcap': 10.435570,
                                            'solarcap': 14.289311,
                                            'nucap': 1.143500,
                                            'x': [0.0, 4.277016, 5.420516, 9.953896, 24.478603, 59.478603],
                                            'y': [0.0, 0.000000, 12.689066, 25.109150, 32.703513, 169.679554],
                                            'arma': REF_ARMA
                                            },
              ('CES', 'No_Storage'):       {'coeffs': (12.403, 0.032),
                                            'windcap': 11.881869,
                                            'solarcap': 9.774715,
                                            'nucap': 5.242805,
                                            'x': [0.0, 4.277016, 9.519821, 11.621728, 16.259835, 51.259835],
                                            'y': [0.0, 0.000000, 12.689066, 25.109150, 32.703513, 169.679554],
                                            'arma': CES_ARMA
                                            },
              ('CES', 'Storage'):          {'coeffs': (12.791, 0.034),
                                            'windcap': 9.774715,
                                            'solarcap': 11.881870,
                                            'nucap': 5.242805,
                                            'x': [0.0, 4.277016, 9.519821, 11.621728, 13.723635, 48.723635],
                                            'y': [0.0, 0.000000, 12.689066, 25.109150, 32.703513, 169.679554],
                                            'arma': CES_ARMA
                                            }}


def step_hist(info, ax, histx, ax_hist):
    x = info['x']
    y = info['y']
    a, b = info['coeffs']

    ax_hist.tick_params(axis='x', labelbottom=False)

    ax.step(x, y, where='post')
    ax.plot(np.arange(min(x), max(x)+1, 1), [a*np.exp(i * b) for i in np.arange(min(x), max(x)+1, 1)], color='red')

    binwidth = 0.25
    xymax = np.max(np.abs(x))
    lim = (int(xymax/binwidth + 1) * binwidth)
    bins = np.arange(0, lim + binwidth, binwidth)
    ax_hist.hist(histx, bins=bins)


def main():

    fig = plt.figure()
    for i, (k, v) in enumerate(CASE_DICT.items()):
        arma_output = v['arma']
        arma_output['WIND_G'] = arma_output['WIND'] * v['windcap']
        arma_output['SOLAR_G'] = arma_output['SOLAR'] * v['solarcap']
        arma_output['VRE'] = arma_output['WIND_G'] + arma_output['SOLAR_G']
        arma_output['NETLOAD'] = arma_output['TOTALLOAD'] - arma_output['VRE']

        x = v['x']
        y = np.array(v['y']) * 1e3
        a, b = v['coeffs']
        x_fit = np.arange(min(x), max(x)+1, 1)
        y_fit = np.array([a*np.exp(i * b) for i in x_fit]) * 1e3

        ax = fig.add_subplot(2,2,i+1)
        ax.hist(arma_output['NETLOAD'], bins=30, color='C1', edgecolor='white', alpha=0.7)
        ax.ticklabel_format(style='sci', scilimits=(0, 5), axis='y')
        ax.set_yticks(np.linspace(*ax.get_ybound(), 8))
        ax.tick_params(axis="y", labelcolor="C1")
        if i == 0 or i == 2:
            ax.set_ylabel('Frequency')
        if i == 2 or i == 3:
            ax.set_xlabel('Load Demand (GW)')



        ax1 = ax.twinx()
        ax1.step(x, y, where='post')
        ax1.plot(x_fit, y_fit, color='C3')
        ax1.text(30, 72*1e3,
                 f"""$\\hat{{y}} = {round(a,3)}e^{{{round(b,3)}x}}$""",
                 color='C3',
                 bbox={'facecolor': 'white', 'alpha': 1, 'pad': 2,},
                 size='large')

        formatter = ticker.StrMethodFormatter("${x:,.0f}")
        ax1.yaxis.set_major_formatter(formatter)
        ax1.set_title(" ".join(k).replace('_', ' '))
        ax1.set_yticks(np.linspace(*ax1.get_ybound(), 8))
        ax1.tick_params(axis="y", labelcolor="C0")
        if i == 1 or i == 3:
            ax1.set_ylabel('Clearing Price ($/GWh)', rotation=-90, va="bottom")
        ax1.grid(None)

    # fig.supxlabel('Load Demand (GW)', fontsize=15, fontweight='bold')
    fig.tight_layout()
    plt.savefig('capacity_cost_histogram.png')



if __name__ == '__main__':
    main()
