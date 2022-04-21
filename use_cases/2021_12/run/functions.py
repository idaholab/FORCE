
import pathlib

import numpy as np
import xarray as xr

# load data at the module level
## find where the data we need is on the path
## this lets us use this file anywhere under "2021/12/run" in the repo
file_path = pathlib.Path(__file__).resolve()
run_index = file_path.parts[::-1].index('run')
data_path = file_path.parents[run_index]/'data'
# get the database
DB_LOC = data_path/'NY_combined.ncdf4'


def _fetch_component(meta, comp_name):
    for comp in meta['HERON']['Components']:
        if comp.name == comp_name:
            return comp

def _build_back_better(ds, meta):
    """
    """
    h2kg = -0.043 * 1000
    comp = _fetch_component(meta, 'H2_storage')
    t = meta['HERON']['time_index']
    activity = meta['HERON']['all_activity'].get_activity(comp, 'charge', 'electricity', t)
    return {'driver': h2kg * activity}, meta


def _build_stack(ds):
  """
    Constructs the stack and clearing prices
    Note ds should only depend on component, not state/year/strategy/price_struct
    @ In, ds, xr.Dataset, capacities and marginal costs
    @ Out, stack, np.array, cumulative capacities as production bins
    @ Out, prices, np.array, prices for each bin
  """
  stacked = ds.sortby(ds['marginal_cost'])
  stack = np.cumsum(stacked['capacity_gw'].values)
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
  sub_ds = ds.sel(state=a, strategy=s, price_struct=p)
  return sub_ds


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


def grid_price(data, meta):
  """
    Determines the clearing price of electricity.
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  ds = xr.open_dataset(DB_LOC, cache=True)
  t = meta['HERON']['time_index']
  # year = meta['HERON']['year_index']
  for comp in meta['HERON']['Components']:
    if comp.name == 'Additional_NPP':
      npp = comp
      break
  else:
    raise RuntimeError
  npp_activity_th = meta['HERON']['all_activity'].get_activity(npp, 'production', 'heat', t)
  npp_activity_e = npp_activity_th * 0.33
  # get the load from the ARMA
  load_e = get_load(data, meta)[0]['electricity']
  # use the stack to derive the electricity price based on the load
  case_ds = _load_case(meta, ds).copy(deep=True)
  exists_cap = case_ds['capacity_gw'].sel(component='Nuclear')
  # if activity is less than the full capacity, "replace" the activity in this copy to get the clearing price
  # if exists_cap:
  #   if exists_cap > npp_activity_e:
  #     # NOTE cannot use isel or sel to set values
  case_ds['capacity_gw'].loc['Nuclear'] = npp_activity_e
  stack, prices, _ = _build_stack(case_ds)
  price, _ = _clearing_price(load_e, stack, prices)
  # Convert stack prices from $/MW to $/GW
  return {'reference_price': price * 1e3}, meta


# DEBUGG
if __name__ == '__main__':
    # Nothing to test here
    pass
