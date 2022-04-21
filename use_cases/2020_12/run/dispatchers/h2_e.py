import os
import sys
import numpy as np

# 43 kW/kgH2 = 4.3e1 kW/kgH2 = 4.3e-2
e_per_h2 = 43e-6 # GW / kgH2

def dispatch(info):
  """
    Dispatches the components based on user-defined algorithms.
    The expected return object is a dict of components, mapped to a dict of
      resources that component uses, mapped to the amount consumed/produced
      as a numpy array.
    Note:
     - Negative values mean the component consumes that resource
     - Positive values mean the component produces that resource
     - The activity doesn't necessarily have to be as long as "time", but it usually should be
    @ In, info, dict, information about the state of the system
    @ Out, activity, dict, activity of components as described above
  """
  heron = info['HERON']
  case = info['HERON']['Case']
  components = dict((c.name, c) for c in heron['Components'])
  sources = heron['Sources']
  func = [x for x in sources if x.is_type('Function')][0]._module
  # is this problem even feasible, i.e., HTSE >= demand?
  ## TODO move to explicit constraint?
  htse_size = components['HTSE'].get_capacity(info)[0]['H2']
  h2_market_size = components['HTSE'].get_capacity(info)[0]['H2']
  if not htse_size >= - h2_market_size:
    raise RuntimeError('Insufficient HTSE size for market size!')
  # load
  load = heron['RAVEN_vars']['TOTALLOAD']
  # case
  labels = heron['Case'].get_labels()
  # H2 price
  price_h2_kg = func.H2_price({}, info)[0]['reference_price']
  # effective $/GW for H2 generation
  price_h2_GW = price_h2_kg / e_per_h2 # $/kgH2 * h2/e -> $/GW

  storage = components['H2_storage']
  initial_stored = storage.get_interaction().get_initial_level(info)
  T = len(load)
  # set up results storage
  activity = {
    'NPP': {'electricity': np.ones(T) * components['NPP'].get_capacity(info)[0]['capacity']},
    'HTSE': {'electricity': np.zeros(T), 'H2': np.zeros(T)},
    'H2_storage': {'H2': np.zeros(T)},
    'grid': {'electricity': np.zeros(T)},
    'H2_market': {'H2': np.zeros(T)}
  }
  # would be nice to set everything at once; due to storage, though, we have inertia
  case_data = func._load_case(info, func.ds)
  stack, prices = func._build_stack(case_data)
  time_param = case.get_time_name()
  for t in range(T):
    if t == 0:
      dt = heron['RAVEN_vars'][time_param][1] - heron['RAVEN_vars'][time_param][0]
      store_level = initial_stored
    else:
      dt = heron['RAVEN_vars'][time_param][t] - heron['RAVEN_vars'][time_param][t-1]
    ld = load[t]
    price_e, _ = func._clearing_price(ld, stack, prices)
    # decisions -> ideally what do we prefer?
    ## if electricity is worth more than h2, make it (vice versa)
    if price_e >= price_h2_GW:
      store_level, activity = dispatch_max_e(activity, info, components, store_level, dt, t)
    else:
      store_level, activity = dispatch_max_h2(activity, info, components, store_level, dt, t)
  return activity

def dispatch_max_e(activity, meta, components, store_level, dt, t):
  """
    Dispatch to maximize electricity production
  """
  # meet the hydrogen customer need, then everything else goes to electricity
  ## remember consuming is negative, so capacity of market is negative
  h2_need = components['H2_market'].get_capacity(meta)[0]['H2']
  ## storage first
  if store_level > 1e-6:
    h2_need_qty = - h2_need * dt # abs total quantity of h2 needed (not rate)
    store_used = min(store_level, h2_need_qty)
    store_rate = store_used / dt
    store_level -= store_used
    activity['H2_storage']['H2'][t] = store_level
    activity['H2_market']['H2'][t] += - store_rate
    h2_need += store_rate # h2_need is negative, store_rate is positive
  ## then htse, if we need more
  if h2_need < 0:
    activity['HTSE']['H2'][t] = - h2_need
    htse_used_e = h2_need * e_per_h2 # two negatives cancel out, net negative
    activity['HTSE']['electricity'][t] = htse_used_e
    activity['H2_market']['H2'][t] += h2_need
  else:
    htse_used_e = 0
  ## everything else to electricity grid
  e_avail = - activity['NPP']['electricity'][t] - htse_used_e
  activity['grid']['electricity'][t] = e_avail
  return store_level, activity

def dispatch_max_h2(activity, meta, components, store_level, dt, t):
  """
    Dispatch to maximize hydrogen production
  """
  e_avail = activity['NPP']['electricity'][t]
  # use HTSE to fill need first
  ## remember consuming is negative, so capacity of market is negative
  h2_need = components['H2_market'].get_capacity(meta)[0]['H2']
  activity['HTSE']['H2'][t] = - h2_need
  htse_used_e = h2_need * e_per_h2 # negatives canceling, net negative
  e_avail += htse_used_e
  activity['HTSE']['electricity'][t] = htse_used_e
  ## how much can storage take?
  store_avail = components['H2_storage'].get_capacity(meta)[0]['H2'] - store_level
  if store_avail > 1e-6:
    # equivalent in power-required-to-make
    store_avail_rate_e = store_avail * e_per_h2 / dt
    store_used_e = min(store_avail_rate_e, e_avail)
    e_avail -= store_used_e
    store_level += store_used_e * dt / e_per_h2
    activity['H2_storage']['H2'][t] = store_level
  # everything else sold at grid TODO flexible operation ... ?
  activity['grid']['electricity'][t] = - e_avail
  return store_level, activity
