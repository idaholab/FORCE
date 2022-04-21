
import pathlib

import numpy as np
import xarray as xr

def load_data():
  file_path = pathlib.Path(__file__).resolve()
  data_path = file_path/'..'/'..'/'data'
  ds = xr.open_dataset(data_path/'IL_combined.ncdf4')
  return ds

def _build_stack(ds):
  stacked = ds.sortby(ds['marginal_cost'])
  stack = np.cumsum(stacked['capacity'].values)
  prices = stacked['marginal_cost'].values
  return stack, prices, stacked.component.values

def _clearing_price(load, stack, prices):
  i = stack.searchsorted(load)
  return prices[i], i

def _load_case(labels, ds):
  a = labels['state']
  s = labels['strategy']
  p = labels['price_struct']
  y = labels['year']
  if y in ds.year:
    sub_ds = ds.sel(state=a, strategy=s, price_struct=p, year=y)
  else:
    sub_ds = ds.sel(state=a, strategy=s, price_struct=p).interp(year=y)
  return sub_ds

def count_usage(load, stack, prices, comp_order):
  usage_indices = stack.searchsorted(load)
  counts_equal= np.bincount(usage_indices, minlength=len(comp_order))
  counts_lte = np.cumsum(counts_equal)[::-1]
  #counts, edges = np.histogram(usage_indices, bins=len(comp_order), range=(0,stack[-2]))
  return counts_lte

def plot_pdc(counts, prices):
  import matplotlib.pyplot as plt
  fig, ax = plt.subplots()
  # first zero count
  first_zero = np.argmax(counts == 0)
  # step plot
  ax.step(counts[:first_zero+1], prices[:first_zero+1]/1000, '.-', where='pre')
  ax.set_xlabel('Hours exceeding price')
  ax.set_ylabel('Electricity price ($/MWh)')
  ax.set_xlim([0, len(load)])
  plt.show()

intMap = {'s': {0: 'CarbonTax', 1: 'Nominal', 2: 'RPS'},
          'p': {0: 'Default', 1: 'LNHR'}}
def run(raven, raven_dict):
  all_load = raven.TOTALLOAD
  index_map = raven._indexMap[0]['TOTALLOAD']
  years = raven.YEAR
  clusters = raven._ROM_Cluster
  all_db = load_data()
  # TODO how to get labels?
  strategy = intMap['s'][raven.strategy[0]]
  price_struct = intMap['p'][raven.price_struct[0]]
  labels = dict(state='IL', strategy=strategy, price_struct=price_struct, year=2025)
  year_index = index_map.index('YEAR')
  cluster_index = index_map.index('_ROM_Cluster')
  slicer = [np.s_[:], np.s_[:],np.s_[:]]
  results = None
  for y, year in enumerate(years):
    counts = None
    labels['year'] = year # ?? +2025?
    case_db = _load_case(labels, all_db)
    slicer[year_index] = y
    for c, cluster in enumerate(clusters):
      slicer[cluster_index] = c
      multiplicity = raven.cluster_multiplicity[y, c]
      load = all_load[tuple(slicer)]
      local_counts, local_prices = get_counts(load, case_db)
      local_counts *= multiplicity
      if results is None:
        results = True
        num_tech = len(local_counts)
        raven.prices = np.zeros((len(years), num_tech))
        raven.counts = np.zeros((len(years), num_tech))
        raven.techs = np.arange(num_tech)
        raven._indexMap = np.atleast_1d({'prices': ['YEAR', 'techs'],
                                         'counts': ['YEAR', 'techs']})
      if counts is None:
        counts = local_counts
        raven.prices[y, :] = local_prices # these don't change in a year
      else:
        counts += local_counts
    # end of cluster loop
    raven.counts[y, :] = counts
  # end of year loop
  raven

def get_counts(load, db):
  stack, prices, comp_order = _build_stack(db)
  counts = count_usage(load, stack, prices, comp_order)
  return counts, prices

if __name__ == '__main__':
  T = 10
  # pull data
  all_db = load_data()
  labels = dict(state='IL', strategy='Nominal', price_struct='Default', year=2025)
  case_db = _load_case(labels, all_db)
  stack, prices, comp_order = _build_stack(case_db)
  # random load
  max_cap = float(case_db.capacity.sum()) - 1000 # skip overflow
  load = np.random.rand(T) * max_cap
  print('DEBUGG load:', load)
  # count usage
  counts = count_usage(load, stack, prices, comp_order)
  plot_pdc(counts, prices)
  print('DEBUGG usage:')
  print('counts, comp, cuml cap, marg price')
  for i, comp in enumerate(comp_order):
    print(' ', counts[i], comp, stack[i], prices[i])

  print('done')

