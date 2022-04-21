"""
  Extracts the 5D capacity and marginal costs of components from the
  slightly-modified EPRI XLSX data
"""

import os
from itertools import islice

# conda installs: xlrd, openpyxl
import numpy as np
import pandas as pd
import xarray as xr
import openpyxl as xl

case_set = False # track whether trimming for the state/strat/price has happened yet

states = ['IL']
strategies = ['Nominal', 'RPS', 'CarbonTax']
price_structs = ['Default', 'LNHR']
years = [2025, 2030, 2035, 2040, 2045, 2050]
# get from xlsx directly below; components = ['clcl-x1', 'clcl-x2', 'clcl-x3', 'clcl-x4', 'clng-r1', 'clng-r2', 'clng-r3', 'cbcf-x1', 'cbcf-x2', 'cbcf-x3', 'cbcf-x4', 'ngcc-x1', 'ngcc-x2', 'ngcc-x3', 'ngcc-n', 'ngst-x', 'nggt-x1', 'nggt-x2', 'nggt-x3', 'nggt-n', 'ptsg-x', 'othc-x', 'h2cc-n', 'h2cc-ig', 'bioe-r1', 'becs-n', 'h2cc-igcs', 'ngcs-n', 'nucl-n1', 'nucl-n2', 'hydr-x', 'wind-r', 'wind-n3', 'wind-n4', 'wind-n5', 'wind-n6', 'wnos-n1', 'pvft-n4', 'pvsx-n4', 'pvdx-n4']

cwd = os.path.abspath(os.path.join(__file__, '..'))
filename = os.path.abspath(os.path.join(cwd, 'from_EPRI','Final Illinois Capacity and Costs.xlsx'))
wb = xl.load_workbook(filename=filename, read_only=True)
ws = wb['CapCost']

# Add overflow component that's not in the workbook.
components = [c.value for c in ws['F1':'AX1'][0]] + ['overflow']

indexers = [states, strategies, price_structs, components, years]
# data_heads = ['capacity', 'marg_cost']
shape = tuple([len(x) for x in indexers])
cap_table = np.zeros(shape, dtype=float)
mgc_table = np.zeros(shape, dtype=float)
# 1:state, 2:strategy, 3:price, 4:component, 5:year

# load capacities, in GW
ci = 'B'
cf = 'AX'
for sp in range(6):
  ri = sp * 8 + 1
  df = pd.read_excel(filename,
      sheet_name='CapCost',
      header=0,
      index_col=[0,1,2,3],
      usecols=f'{ci}:{cf}',
      skiprows=ri-1,
      nrows=6).fillna(0)
  # Assign overflow component for times when load exceeds stack.
  df = df.assign(overflow = 1000.0)
  identifier = df.index[0][:3]
  t = states.index(identifier[0])
  s = strategies.index(identifier[1])
  p = price_structs.index(identifier[2])
  cap_table[t, s, p, :, :] = df.values.T

# load marginal prices, initially in $/MW
ci = 'BA'
cf = 'CT'
for t, state in enumerate(states):
  for s, strategy in enumerate(strategies):
    for p, struct in enumerate(price_structs):
      if strategy == 'CarbonTax':
        ri = 1
      else:
        ri = 17
      df = pd.read_excel(filename,
          sheet_name='CapCost',
          header=0,
          index_col=[0],
          usecols=f'{ci}:{cf}',
          skiprows=ri-1,
          nrows=6).fillna(0)
      # Assign overflow component for times when load exceeds stack.
      df = df.assign(overflow = 1000.0)
      table_part = mgc_table[t, s, p, :, :]
      mgc_table[t, s, p, :, :] = df.values.T * 1000 # $/MW to $/GW

# 1:state, 2:strategy, 3:price, 4:component, 5:year
coords = {'state': states,
          'strategy': strategies,
          'price_struct': price_structs,
          'component': components,
          'year': years}
cap_DA = xr.DataArray(cap_table, coords=coords, dims=list(coords.keys()), name='capacity')
mgc_DA = xr.DataArray(mgc_table, coords=coords, dims=list(coords.keys()), name='marginal_cost')

# customize nuclear margins
mgc_DA.loc['IL', :, :, ['nucl-x', 'nucl-n1', 'nucl-n2'], :] *= 1e-10
# customize VRE margins for PTC
VREs = ['wind-r','wind-n3','wind-n4','wind-n5','wind-n6','wnos-n1','pvft-n3','pvft-n4','pvsx-n3','pvsx-n4','pvdx-n3','pvdx-n4']
mgc_DA.loc['IL', :, :, VREs, :] -= 17000

ds = xr.Dataset({'capacity': cap_DA, 'marginal_cost': mgc_DA})
# interpolate years
ds = ds.interp(year=np.arange(min(years), max(years)+1))
ds.to_netcdf(cwd+'/IL_combined.ncdf4')
print(f'Wrote {cwd+"/IL_combined.ncdf4"}')


# collapse for regulated case
techmap = {
  'coal': 'clcl-x1|clcl-x2|clcl-x3|clcl-x4|clng-r1|clng-r2|clng-r3|clng-r4|cbcf-x1|cbcf-x2|cbcf-x3|cbcf-x4'.split('|'),
  'gas': 'ngcc-x1|ngcc-x2|ngcc-x3|ngcc-n|ngst-x|nggt-x1|nggt-x2|nggt-x3|nggt-n|ngcs-n'.split('|'),
  'petrol': ['ptsg-x', 'overflow'],
  'other': ['othc-x', 'bioe-r1', 'becs-n'],
  'h2gen': ['h2cc-n', 'h2cc-ig', 'h2cc-igcs'],
  'nuclear': ['nucl-n1', 'nucl-n2', 'nucl-x'],
  'VRE': 'hydr-x|wind-r|wind-n3|wind-n4|wind-n5|wind-n6|wnos-n1|pvft-n4|pvsx-n4|pvdx-n4'.split('|'),
}

# DEBUG
## select the subset
arrays = {}
comp_ax = list(ds.capacity.dims).index('component')
for t, (tech, members) in enumerate(techmap.items()):
  subset = ds.sel(component=members)
  caps = subset.capacity.sum(dim='component')# .expand_dims(axis=comp_ax, component=[tech])
  costs = (subset.capacity / caps * subset.marginal_cost).sum(dim='component').expand_dims(axis=comp_ax, component=[tech])
  caps = caps.expand_dims(axis=comp_ax, component=[tech])
  new = xr.Dataset({'capacity': caps, 'marginal_cost': costs})
  if t == 0:
    truncated = new
  else:
    truncated = truncated.merge(new)

truncated.to_netcdf(cwd+'/IL_truncated.ncdf4')
print(f'Wrote {cwd+"/IL_truncated.ncdf4"}')

print('done')

