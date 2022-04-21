#!/usr/bin/env python
"""
Capacity and Costs Processing Script
"""
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib as mpl
# mpl.rcParams['text.usetex'] = True
mpl.use('Agg') # Prevents the script from blocking while plotting
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import chisquare

plt.rc("figure", figsize=(15, 5))
plt.rc(
    "axes",
    titlesize=15,
    titleweight="bold",
    labelsize=20,
    axisbelow=True,
    grid=True
)
plt.rc("savefig", bbox="tight")
plt.rc("legend", fontsize=20)
plt.rc(["xtick", "ytick"], labelsize=15)


DATA_DIR = Path('../data/from_EPRI').resolve()

CASE_DICT = {('Reference', 'No_Storage'): {'coeffs': (12.791, 0.025),
                                           'windcap': 10.435570,
                                           'solarcap': 14.894274,
                                           'nucap': 1.143500},

              ('Reference', 'Storage'):    {'coeffs': (12.881, 0.026),
                                            'windcap': 10.435570,
                                            'solarcap': 14.289311,
                                            'nucap': 1.143500},

              ('CES', 'No_Storage'):       {'coeffs': (12.403, 0.032),
                                            'windcap': 11.881869,
                                            'solarcap': 9.774715,
                                            'nucap': 5.242805},

              ('CES', 'Storage'):          {'coeffs': (12.791, 0.034),
                                            'windcap': 9.774715,
                                            'solarcap': 11.881870,
                                            'nucap': 5.242805}}



def map_cost_to_cap(energy_type):
    """
    Return a mapped value Technology Type => Category Type

    @In: energy_type, string, an expected technology type
    @Out: k, string, a broader category the technology falls into.
    """
    mapper = {
        'Nuclear': ['nuca-n', 'nucl-n2', 'nucl-x'],
        'Other (Bioenergy)': ['bioe-r3'],
        'BECCS': ['becs-n'],
        'NGCC': ['ngcc-x1', 'ngcc-x2', 'ngcc-x3'],
        'NGGT': ['nggt-n', 'nggt-x1', 'nggt-x2', 'ngst-x', 'clng-r3'],
        'Hydro': ['hydr-x'],
        'Wind': ['wind-n2', 'wind-n3', 'wind-n4', 'wind-n5', 'wind-r', 'wnos-n1', 'wnos-n2'],
        'Solar': ['pvft-n4', 'pvft-n5', 'pvft-x', 'pvdx-n4', 'pvdx-n5', 'pvsx-n4', 'pvsx-n5'],
        'Overflow': ['ptsg-x']
    }
    for k, v in mapper.items():
        if energy_type in v:
            return k

def main():
    costs = pd.read_excel(
        DATA_DIR/'Costs.xlsx',
        sheet_name='Variable Cost',
        header=0,
        names=['type', 'detailed_description', 'marginal_cost'],
        nrows=30,
        engine='openpyxl'
    )

    capacities = pd.read_excel(
        DATA_DIR/'Generation.xlsx',
        sheet_name='Capacity',
        header=0,
        usecols='A:P',
        nrows=4,
        engine='openpyxl'
    )

    # Compute average marginal cost for categories with > 1 technology
    costs['Category'] = costs['type'].apply(lambda x: map_cost_to_cap(x))
    costs = costs.groupby('Category').agg({'marginal_cost': 'mean'})

    capacities = capacities.rename(columns={'NY Capacity -GW': 'Case'})
    capacities = capacities.assign(
        # Combine Solar Values into one Solar Category.
        Solar = lambda x: x['Utility Scale PV'] + x['Rooftop Solar'],
        # This is the max TOTALLOAD in our synth histories
        Overflow = 35
    )

    # Remove columns that we are not going to use in this analysis
    drop_cols = ['Coal', 'Coal CCS', 'NG CCS', 'Utility Scale PV',
                 'Rooftop Solar', 'Pumped Hydropower Storage', 'Li-Ion Battery',
                 'Hydrogen', 'Other (Bioenergy)', 'BECCS',]
    capacities = capacities.drop(columns=drop_cols)

    # Pivot table from wide to tall format
    capacities = pd.melt(capacities, id_vars='Case', var_name='Category', value_name='capacity_gw')

    # Set the order of the categorical index variables
    case_levels = ['Reference - No Storage', 'Reference - Storage', 'CES - No Storage', 'CES - Storage']
    category_levels = ['Solar', 'Wind', 'Hydro', 'Nuclear', 'NGCC', 'NGGT', 'Overflow']
    capacities.Case = capacities.Case.astype("category")
    capacities.Case = capacities.Case.cat.set_categories(case_levels)
    capacities.Category = capacities.Category.astype("category")
    capacities.Category = capacities.Category.cat.set_categories(category_levels)
    capacities = capacities.set_index(['Case', 'Category']).sort_index()

    # Create the stack
    stack = capacities.join(costs)

    # We only want to start cumulating capacity starting at Hydro,
    # and skip Solar & Wind.
    stack['chained_capacity'] = (stack
                                 .groupby('Case')['capacity_gw']
                                 .transform(lambda x: x.shift(-2).cumsum().shift(2)))

    ####
    # Plotting Portion (not needed for building the stack)
    ####
    fig = plt.figure(tight_layout=True)
    for i,(k,d) in enumerate(stack.groupby('Case')):
        # Answer taken from here:
        # https://stackoverflow.com/questions/57278394/python-how-to-generate-additional-values-between-two-row-values-in-a-dataframe
        line_ins = 20
        res_dict = {col: [y for val in d[col] for y in [val] + [np.nan]*line_ins][:-line_ins] for col in d.columns}
        df_new = pd.DataFrame(res_dict)
        df_new['chained_capacity'] = df_new['chained_capacity'].interpolate()
        df_new['marginal_cost'] = df_new['marginal_cost'].interpolate(method='pad')
        df_new['capacity_gw'] = df_new['capacity_gw'].interpolate(method='pad')
        df_new = df_new.dropna()
        df_new = df_new.query('marginal_cost > 0')

        # We'll fit an exponential curve to this data
        x = df_new['chained_capacity'].to_numpy()
        y = df_new['marginal_cost'].to_numpy()
        popt, _ = curve_fit(lambda t,a,b: a * np.exp(b * t), x, y, p0=(8, 0.05))

        # Let's compute R^2
        resid = y - (lambda t,a,b: a * np.exp(b * t))(x, *popt)
        ss_res = np.sum(resid**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot)

        # Let's grab the ARMA output to underlay demand histogram
        if 'Reference' in k:
            arma_output_path = Path('../train/ny_default_load/Output/synth.csv').resolve()
        else:
            arma_output_path = Path('../train/ny_ces_load/Output/synth.csv').resolve()

        arma_output = pd.read_csv(arma_output_path)
        new_key = tuple(i.replace(' ', '_') for i in k.split(' - '))
        arma_output['WIND_G'] = arma_output['WIND'] * CASE_DICT[new_key]['windcap']
        arma_output['SOLAR_G'] = arma_output['SOLAR'] * CASE_DICT[new_key]['solarcap']
        arma_output['VRE'] = arma_output['WIND_G'] + arma_output['SOLAR_G']
        arma_output['NETLOAD'] = arma_output['TOTALLOAD'] - arma_output['VRE']


        # Now let's make the plots
        ax = fig.add_subplot(1,4,i+1)
        ax.plot(x, y, '.-')
        ax.plot(x, (lambda t,a,b: a * np.exp(b * t))(x, *popt), 'r-')
        ax1 = ax.twinx()
        ax1.hist(arma_output['NETLOAD'], bins=30, alpha=0.5)
        ax.text(10, 60,
                f"""$\\hat{{y}} = {round(popt[0],3)}e^{{{round(popt[-1],3)}x}}$\n$R^2 = {round(r_squared, 4)}$""",
                bbox={'facecolor': 'white', 'alpha': 1, 'pad': 2},
                size='large')
        ax.set_title(k)
        ax.set_xticks(np.arange(0, 70, 10))

    print('Saving image to: capacity_cost_fit.png')
    fig.supxlabel('Load (GW)')
    fig.supylabel('Clearing Price ($)')
    plt.savefig('capacity_cost_fit.png')

    # # We need to recreate the MultiIndex to match last years stack.
    # # This will save us effort of changing the functions.py file.
    # stack.index = pd.MultiIndex.from_product([
    #     ['NY'],
    #     ['Reference', 'CES'],
    #     ['Storage', 'No_Storage'],
    #     ['Solar', 'Wind', 'Hydro', 'Nuclear', 'NGCC', 'NGGT', 'Overflow']
    # ], names=['state', 'price_struct', 'strategy', 'component'])
    #
    # stack = stack.drop(columns=['chained_capacity'])
    #
    # new_idx = pd.MultiIndex.from_product([
    #     ['NY'],
    #     ['Reference', 'CES'],
    #     ['Storage', 'No Storage'],
    #     ['Solar', 'Wind', 'Hydro', 'Nuclear', 'NGCC', 'NGGT', 'Overflow'],
    #     np.arange(2020, 2051, 1)
    # ], names=['state', 'price_struct', 'strategy', 'component', 'year'])
    #
    # stack = stack.reindex(new_idx)
    #
    # stack = stack.query("component not in ['Solar', 'Wind']")
    print(stack)
    #
    # stack.to_csv(DATA_DIR.parent/'NY_combined.csv')

    # Save to xarray because other scripts depend on the stack being in ncdf4.
    stack_xarr = stack.to_xarray()
    stack_xarr.to_netcdf(DATA_DIR.parent/'NY_combined.ncdf4')

if __name__ == '__main__':
    main()
