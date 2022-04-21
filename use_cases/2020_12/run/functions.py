
import pathlib

import numpy as np
import xarray as xr
from scipy.interpolate import interp1d

try:
  profile
except NameError:
  profile = lambda f: f

# load data at the module level
## find where the data we need is on the path
## this lets us use this file anywhere under "2020/12/run" in the repo
file_path = pathlib.Path(__file__).resolve()
run_index = file_path.parts[::-1].index('run')
data_path = file_path.parents[run_index]/'data'
# get the database
db_loc = data_path/'IL_combined.ncdf4'
ds = xr.open_dataset(db_loc)
# interpolation note: da = ds['Capacity'].interp(year=2028)
# TODO should all interpolation be done a priori then stored in the DB?
#  -> should this maybe be done by the netcdf-writing script?
# TODO drop all 0-capacity entries? Maybe do this on a by-year/case basis.

# Define Coefficients for each year (From the linear regression of H2A outputs used in the exelon 2019 report)
regCoeffs = {2025 : [1.186280496, 9.33443E-06, 1.3039682],
             2030 : [1.153753506, 9.64470E-06, 1.360744923],
             2035 : [1.15950, 9.19638E-06, 1.37053],
             2040 : [1.1420, 9.18287E-06, 1.38268],
             2045 : [1.110779085, 8.76672E-06, 1.39591],
             2050 : [1.061372505, 8.13562E-06, 1.43535]}
# generate interpolator
h2_coefs = []
for c in range(3):
  data = list(zip(*((key, val[c]) for key, val in regCoeffs.items())))
  h2_coefs.append(interp1d(data[0], data[1]))

def _build_stack(ds):
  """
    Constructs the stack and clearing prices
    Note ds should only depend on component, not state/year/strategy/price_struct
    @ In, ds, xr.Dataset, capacities and marginal costs
    @ Out, stack, np.array, cumulative capacities as production bins
    @ Out, prices, np.array, prices for each bin
  """
  stacked = ds.sortby(ds['marginal_cost'])
  stack = np.cumsum(stacked['capacity'].values)
  prices = stacked['marginal_cost'].values
  return stack, prices, stacked.component.values

def _clearing_price(load, stack, prices):
  """
    Gets the clearing price based on the load
    TODO
  """
  # load is in GW, stack is in MW -> change stack to GW
  i = stack.searchsorted(load)
  return prices[i], i

@profile
def _load_case(meta, ds):
  """
    Trims data down to current case
    @ In, meta, dict, analysis case info
    @ In, ds, xr.DataSet, capacities and marginal costs
    @ Out, sub_ds, xr.DataSet, trimmed dataset
  """
  labels = meta['HERON']['Case'].get_labels()
  a = labels['state']
  s = labels['strategy']
  p = labels['price_struct']
  y = meta['HERON']['active_index']['year'] + 2025
  if y in ds.year:
    sub_ds = ds.sel(state=a, strategy=s, price_struct=p, year=y)
  else:
    sub_ds = ds.sel(state=a, strategy=s, price_struct=p).interp(year=y)
  return sub_ds

@profile
def NPP_cap(data, meta):
  """
    Provides the capacity of the collective NPP unit.
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  caps = _load_case(meta, ds)['capacity']
  nuc_cap = caps.sel(component=['nucl-x', 'nucl-n1', 'nucl-n2']).values.sum()
  return {'electricity': nuc_cap}, meta

def get_load(data, meta):
  """
    Acquires the electric load
    Might be reducable to just the ARMA
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  load = meta['HERON']['RAVEN_vars']['TOTALLOAD']
  t = meta['HERON']['time_index']
  return {'electricity': load[t]}, meta

def e_consume(data, meta):
  """
    Flips the sign of electricity consumed for cash flows.
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  activity = - meta['HERON']['activity']['electricity']
  data = {'driver': activity}
  return data, meta

def H2_activity(data, meta):
  """
    Flips the sign of hydrogen consumed for cash flows.
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  activity = meta['HERON']['activity']['H2']
  data = {'driver': activity}
  return data, meta

def secondary_activity(data, meta):
  """
    Returns activity of named component
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  data = {'driver': meta['HERON']['activity']['electricity']}
  return data, meta

def penalty_activity(data, meta):
  """
    Returns activity of named component
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  data = {'driver': meta['HERON']['activity']['electricity']}
  return data, meta

@profile
def grid_price(data, meta):
  """
    Determines the clearing price of electricity.
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  t = meta['HERON']['time_index']
  for comp in meta['HERON']['Components']:
    if comp.name == 'NPP':
      npp = comp
      break
  else:
    raise RuntimeError
  npp_activity = meta['HERON']['all_activity'].get_activity(npp, 'electricity', t)
  # get the load from the ARMA
  load = get_load(data, meta)[0]['electricity']
  # use the stack to derive the electricity price based on the load
  case_ds = _load_case(meta, ds).copy(deep=True)
  # note n1 never gets used
  # further note existing nuc and new nuc are never present in the same year
  exists_cap = case_ds['capacity'].sel(component='nucl-x')
  n2_cap = case_ds['capacity'].sel(component='nucl-x')
  # if activity is less than the full capacity, "replace" the activity in this copy to get the clearing price
  if exists_cap:
    if exists_cap > npp_activity:
      # NOTE cannot use isel or sel to set values
      case_ds['capacity'].loc['nucl-x'] = npp_activity
  elif n2_cap:
    if n2_cap > npp_activity:
      case_ds['capacity'].loc['nucl-n2'] = npp_activity
  stack, prices, _ = _build_stack(case_ds)
  price, _ = _clearing_price(load, stack, prices)
  return {'reference_price': price}, meta

@profile
def H2_price(data, meta):
  """
    Determines the going price for hydrogen
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  # Get simulation year
  y = int(meta['HERON']['active_index']['year'])

  # Get H2 market size
  ## kgH2 / s -> kgH2 / day
  size = abs(meta['HERON']['RAVEN_vars']['H2_market_capacity']) * 86400

  # Calculate the H2 Price
  # equation has form y = a*e^(-bx)+c
  a = h2_coefs[0](y + 2025)
  b = h2_coefs[1](y + 2025)
  c = h2_coefs[2](y + 2025)
  try:
      H2Price = a * np.exp(- b * size) + c
  except:
      raise Exception('Incorrect year input. Acceptable years: 2025-2050, every 5 years')

  return {'reference_price': float(H2Price)}, meta

def constrain(raven):
  """
    match HTSE and H2 market sizes
  """
  # HTSE_capacity is positive
  # H2_market_capacity is negative
  # both are in units of kg H2/s
  # we want HTSE > market size
  return True
  # OLD
  if hasattr(raven, 'HTSE_built_capacity'):
    htse = raven.HTSE_built_capacity
  else:
    htse = raven.HTSE_capacity
  return abs(htse) - abs(raven.H2_market_capacity) >= 0.0

###### regulated case functions

# truncations have happened in the extract_cap_marg.py script to save time here
# techmap = {
#   'coal': 'clcl-x1|clcl-x2|clcl-x3|clcl-x4|clng-r1|clng-r2|clng-r3|clng-r4|cbcf-x1|cbcf-x2|cbcf-x3|cbcf-x4'.split('|'),
#   'gas': 'ngcc-x1|ngcc-x2|ngcc-x3|ngcc-n|ngst-x|nggt-x1|nggt-x2|nggt-x3|nggt-n|ngcs-n'.split('|'),
#   'petrol': ['ptsg-x'],
#   'other': ['othc-x', 'bioe-r1', 'becs-n'],
#   'h2gen': ['h2cc-n', 'h2cc-ig', 'h2cc-igcs'],
#   'nuclear': ['nucl-n1', 'nucl-n2', 'nucl-x'],
#   'VRE': 'hydr-x|wind-r|wind-n3|wind-n4|wind-n5|wind-n6|wnos-n1|pvft-n4|pvsx-n4|pvdx-n4'.split('|'),
# }

trunc_loc = data_path/'IL_truncated.ncdf4'
trunc = xr.open_dataset(trunc_loc)

def get_e_activity(data, meta):
  """
    Returns activity of named component
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  data = {'driver': meta['HERON']['activity']['electricity']}
  return data, meta

def get_trunc_cap(ds, meta, comp):
  """
    Determines the going capacity for this technology
    @ In, ds, xr.Dataset, dataset with component info
    @ In, meta, dict, state information
    @ In, comp, str, component to return info for
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  sub = _load_case(meta, ds)
  return float(sub.capacity.sel(component=comp))
def get_coal_cap(data, meta):
  """
    Determines the going capacity for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'electricity': get_trunc_cap(trunc, meta, 'coal')}, meta
def get_gas_cap(data, meta):
  """
    Determines the going capacity for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'electricity': get_trunc_cap(trunc, meta, 'gas')}, meta
def get_petrol_cap(data, meta):
  """
    Determines the going capacity for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'electricity': get_trunc_cap(trunc, meta, 'petrol')}, meta
def get_other_cap(data, meta):
  """
    Determines the going capacity for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'electricity': get_trunc_cap(trunc, meta, 'other')}, meta
def get_h2gen_cap(data, meta):
  """
    Determines the going capacity for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'electricity': get_trunc_cap(trunc, meta, 'h2gen')}, meta
def get_nuclear_cap(data, meta):
  """
    Determines the going capacity for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'electricity': get_trunc_cap(trunc, meta, 'nuclear')}, meta
def get_VRE_cap(data, meta):
  """
    Determines the going capacity for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'electricity': get_trunc_cap(trunc, meta, 'VRE')}, meta

def get_trunc_mgc(ds, meta, comp):
  """
    Determines the going marginal cost for this technology
    @ In, ds, xr.Dataset, dataset with component info
    @ In, meta, dict, state information
    @ In, comp, str, component to return info for
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  sub = _load_case(meta, ds)
  return -1 * float(sub.marginal_cost.sel(component=comp))
def get_coal_mgc(data, meta):
  """
    Determines the going marginal_cost for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'reference_price': get_trunc_mgc(trunc, meta, 'coal')}, meta
def get_gas_mgc(data, meta):
  """
    Determines the going marginal_cost for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'reference_price': get_trunc_mgc(trunc, meta, 'gas')}, meta
def get_petrol_mgc(data, meta):
  """
    Determines the going marginal_cost for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'reference_price': get_trunc_mgc(trunc, meta, 'petrol')}, meta
def get_other_mgc(data, meta):
  """
    Determines the going marginal_cost for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'reference_price': get_trunc_mgc(trunc, meta, 'other')}, meta
def get_h2gen_mgc(data, meta):
  """
    Determines the going marginal_cost for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'reference_price': get_trunc_mgc(trunc, meta, 'h2gen')}, meta
def get_nuclear_mgc(data, meta):
  """
    Determines the going marginal_cost for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'reference_price': get_trunc_mgc(trunc, meta, 'nuclear')}, meta
def get_VRE_mgc(data, meta):
  """
    Determines the going marginal_cost for this technology
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  return {'reference_price': get_trunc_mgc(trunc, meta, 'VRE')}, meta

def get_HTSE_cap(data, meta):
  # nominally, we can use the whole HTSE
  built_h2 = meta['HERON']['RAVEN_vars']['HTSE_built_capacity'] # in kgH2/s
  # but since IES, we limit it to the size of the nuclear plant
  # npp_limit_e = get_nuclear_cap(data, meta)[0]['electricity'] # in GW
  # npp_limit_h2 = npp_limit_e / 43e-6 / 3600 # 43e-6 GWh/kgH2, want per second not per hour
  # return {'H2': min(built_h2, npp_limit_h2)}, meta
  return {'H2': built_h2}, meta

def get_HTSE_cap_driver(data, meta):
  return {'driver': meta['HERON']['RAVEN_vars']['HTSE_built_capacity']}, meta

def get_HTSE_cap_from_delta(data, meta):
  market_cap = float(meta['HERON']['RAVEN_vars']['H2_market_capacity'])
  delta = meta['HERON']['RAVEN_vars']['IES_delta_cap']
  return {'H2': - market_cap + delta}, meta

def get_HTSE_cap_from_delta_driver(data, meta):
  cap = get_HTSE_cap_from_delta(data, meta)[0]['H2']
  return {'driver': cap}, meta

# DEBUGG
if __name__ == '__main__':
  case = dict(year=2030, state='IL', strategy='CarbonTax', price_struct='LNHR')
  import timeit, copy
  trial = ds.sel(**case)
  N = int(1e3)
  timing = timeit.timeit(lambda: ds.sel(**case), number=N)
  print('full case timing:', timing)
  subcase = copy.deepcopy(case)
  subcase.pop('year')
  subds = ds.sel(**subcase)
  remainder = {'year': 2030}
  trial2 = subds.sel(**remainder)
  timing2 = timeit.timeit(lambda: subds.sel(**remainder), number=N)
  print('partial case timing:', timing2)
  print(f'rel diff: {2*(timing-timing2)/(timing+timing2):1.9e}')
  print('')
  # data = trial.sel(component=['nucl-x', 'nucl-n2', 'nucl-n1'])
  # print('A:', data)
  # print('0:', data['capacity'] > 1e-6)
  print('orig:', trial.component)
  data = trial.where(trial['capacity'] > 1e-6, drop=True)
  print('trim:', data.component)
  active = [x for x in data.component.values if x.startswith('nucl')][0]
  active = next((val for idx, val in np.ndenumerate(data.component.values) if val.startswith('nucl')))
  print('active:', active)
  margin = float(data['marginal_cost'].loc[active])#.values[0]
  print('margin:', margin)
  stack, prices, comp_order = _build_stack(data)
  print(' - Stack -')
  print('case:', case)
  print('i, load (GW), clearing price ($/MWh)')
  for i, load in enumerate(stack):
    print(i, load, prices[i], comp_order[i])
  print(' - end stack -')
  print('Clearing price check: load (GW), clearing price ($/GWh)')
  loads = np.asarray([0, 5, 10, 20, 30])
  for load in loads:
    clear, idx = _clearing_price(load, stack, prices)
    print(load, clear)
