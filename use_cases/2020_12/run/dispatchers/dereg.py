import os
import sys
from functools import partial

import numpy as np
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 43 kWh/kgH2 = 4.3e1 kWh/kgH2
e_per_h2 = 43e-6 # GWh / kgH2

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
  # load
  load = heron['RAVEN_vars']['TOTALLOAD']
  # case
  # labels = heron['Case'].get_labels()
  # H2 price
  price_h2_kg = func.H2_price({}, info)[0]['reference_price'] # $/kg
  # effective $/GW for H2 generation
  price_h2_GWh = price_h2_kg / e_per_h2 # $/GW = $/kg * kg/GWh

  # In this deregulated approach, the NPP gets to submit its bid
  #   at whatever level it wants, at the risk of not being dispatched.
  #   The bid is the price ($/GW) and the capacity at that price (GW)
  #   After that, the ISO decides when to call on it, and the NPP is committed
  #   for whatever it bid (price  and capacity).
  # NPP bid is NPP marginal cost + H2 opp cost + "adder"
  all_data = func.ds
  data = func._load_case(info, all_data)
  data = data.where(data.capacity > 1e-6, drop=True)
  # since only one nuclear exists (propert of THIS dataset), figure out which one it is
  try:
    npp = next((val for idx, val in np.ndenumerate(data.component.values) if val.startswith('nucl')))
  except StopIteration:
    npp = None
  # npp marginal cost, just take whichever one is nonzero (cheating)
  if npp is None:
    NPP_bid =1e9
  else:
    NPP_mc = float(data['marginal_cost'].loc[npp])
    # hydrogen opportunity cost = h2 price $/kg-s * kg-s/MW@HTSE - HTSE $/MW
    ## but HTSE var O&M is functionally zero since it's on hot standby (Konor)
    H2_opp = price_h2_GWh - NPP_mc
    NPP_bid = NPP_mc + H2_opp + info['HERON']['RAVEN_vars']['NPP_bid_adjust']
    data['marginal_cost'].loc[npp] = float(NPP_bid) # float cuz np 0d arrays
  # rebuild the stack, prices based on this nuclear bid
  stack, prices, comp_order = func._build_stack(data)
  # NOTE this ceases the NPP's control over its future.
  ## Once it submits bid prices, the ISO takes over and calls on it to
  ## be dispatched whenever it sees fit. The NPP doesn't get to know the prices
  ## or load a priori, it just gets to bid in.

  # Now we act as the ISO, for actual dispatch requests each hour.
  ## Note for this dereg case the ISO doesn't care about the hydrogen side of things.
  # set up results storage
  market_cap = components['H2_market'].get_capacity(info)[0]['H2'] # negative
  if npp is None:
    npp_cap = 0
  else:
    npp_cap = components['NPP'].get_capacity(info)[0]['electricity'] # positive
  htse_cap_h2 = components['HTSE'].get_capacity(info)[0]['H2']     # positive
  store_cap = components['H2_storage'].get_capacity(info)[0]['H2'] # positive
  store_initial = components['H2_storage'].get_interaction().get_initial_level(info)
  T = len(load)
  activity = {
    'NPP': {'electricity': np.ones(T) * npp_cap},
    'HTSE': {'electricity': None, 'H2': None},
    'H2_storage': {'H2': None},
    'grid': {'electricity': np.zeros(T)},
    'H2_market': {'H2': np.ones(T) * market_cap},
    'Secondary': {'electricity': None},
    'E_Penalty': {'electricity': None},
  }
  # dispatch NPP over the 24 hours given
  stack_usage_indices = stack.searchsorted(load)
  if npp is None:
    # we have no nuclear, so grid doesn't use any npp electricity
    activity['grid']['electricity'][:] = 0.0
  else:
    npp_index = next((idx for idx, val in np.ndenumerate(stack) if comp_order[idx] == npp))[0]
    # whenever npp is fully committed, we make all the e-
    e_mask = stack_usage_indices > npp_index
    activity['grid']['electricity'][e_mask] = -1 * npp_cap
    # when partially committed, commit what we need to
    e_partial = stack_usage_indices == npp_index
    activity['grid']['electricity'][e_partial] = -1 * (load[e_partial] - stack[npp_index - 1])
    # when not dispatched, we already zero
  # to do the rest, we build a little pyomo optimization
  # model
  m = pyo.ConcreteModel()
  # indices
  Ts = np.arange(0, T, dtype=int)
  m.T = pyo.Set(initialize=Ts)
  # optimization variables
  ## using bounds "as intended"
  # htse_bounds = lambda m, i: (0, htse_cap_h2)
  # secm_bounds = lambda m, i: (0, 1e4)
  # stor_bounds = lambda m, i: (-store_cap/3600, store_cap/3600)
  # m.HTSE = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=htse_bounds, initialize=0) # units kgH2/s
  # m.SecM = pyo.Var(m.T, within=pyo.NonNegativeReals, bounds=secm_bounds, initialize=0) # units GW
  # m.Stor = pyo.Var(m.T, within=pyo.Reals, bounds=stor_bounds, initialize=0)            # units kgH2/s, NOT current amount stored
  ## manually set constraint bounds
  m.HTSE = pyo.Var(m.T, within=pyo.NonNegativeReals, initialize=0) # units kgH2/s
  m.SecM = pyo.Var(m.T, within=pyo.NonNegativeReals, initialize=0) # units GW
  m.Stor = pyo.Var(m.T, within=pyo.Reals, initialize=0)            # units kgH2/s, NOT current amount stored
  m.E_dump = pyo.Var(m.T, within=pyo.NonNegativeReals, initialize=0)
  m.HTSE_cap = pyo.Constraint(m.T, rule=lambda m, t: m.HTSE[t] <= htse_cap_h2) # kg/s
  m.SecM_cap = pyo.Constraint(m.T, rule=lambda m, t: m.SecM[t] <= 1e4)         # GW
  m.Stor_low = pyo.Constraint(m.T, rule=lambda m, t: m.Stor[t] >= -store_cap/3600) # kg/s
  m.Stor_high = pyo.Constraint(m.T, rule=lambda m, t: m.Stor[t] <= store_cap/3600) # kg/s
  m.E_dump_cap = pyo.Constraint(m.T, rule=lambda m, t: m.E_dump[t] <= 1e2)
  # optimization objective
  rule = partial(opt_obj, stack, prices, load, activity['NPP']['electricity'], activity['grid']['electricity'])
  m.objective = pyo.Objective(rule=rule, sense=pyo.minimize)
  # constraints
  ## storage bounds, 0 < STORE[t-1] + 3600 * (HTSE[t] - H2_MARKET_CAP) < STORE_CAP
  rule = partial(opt_store, store_initial, store_cap)
  m.StoreCap = pyo.Constraint(m.T, rule=rule)
  ## H2 market is satisfied (HTSE_H2 + STORE_H2/3600 == H2_MARKET_CAP)
  rule = lambda m, t: m.HTSE[t] + m.Stor[t] + market_cap == 0
  m.H2_consv = pyo.Constraint(m.T, rule=rule)
  ## consv. e-, sinks == sources: E_dump(t) + HTSE_H2(t) * e_per_h2 = NPP_to_h(t) + SecMark(t)
  rule = lambda m, t: m.E_dump[t] + m.HTSE[t] * e_per_h2 * 3600 == (npp_cap + activity['grid']['electricity'][t]) + m.SecM[t]
  # rule = lambda m, t: m.E_dump[t] + m.HTSE[t] * e_per_h2 * 3600 - activity['grid']['electricity'][t]== npp_cap + m.SecM[t]
  m.E_consv = pyo.Constraint(m.T, rule=rule)

  #debug_setup_print(activity, m, stack, prices, comp_order, load,
  #                  htse_cap_h2, npp_cap, store_cap, store_initial, market_cap,
  #                  price_h2_kg, price_h2_GW, NPP_bid, H2_opp,info['HERON']['RAVEN_vars']['NPP_bid_adjust'])
  soln = pyo.SolverFactory('cbc').solve(m)
  if soln.solver.status == SolverStatus.ok and soln.solver.termination_condition == TerminationCondition.optimal:
    print('Successful hydrogen optimization solve.')
    #debug_pyomo_soln(m)
  else:
    print('Storage optimization FAILURE!')
    print(' ... status:', soln.solver.status)
    print(' ... termination:', soln.solver.termination_condition)
    m.pprint()
    debug_setup_print(activity, m, stack, prices, comp_order, load,
                    htse_cap_h2, npp_cap, store_cap, store_initial, market_cap,
                    price_h2_kg, price_h2_GWh, NPP_bid, H2_opp,info['HERON']['RAVEN_vars']['NPP_bid_adjust'])
    raise RuntimeError('Failed hydrogen solve!')
  # store activity
  # NOTE for SecM and E_dump we directly include prices here rather than recalculate them in TEAL,
  #      since we have the load data now and won't have it (as accessible) then.
  for var in m.component_objects(pyo.Var):
    data = np.asarray([var[t].value for t in Ts])
    if var.name == 'HTSE':
      activity['HTSE']['H2'] = data
      activity['HTSE']['electricity'] = - data * e_per_h2 * 3600
    elif var.name == 'SecM':
      new_load = load + data
      indices = stack.searchsorted(new_load)
      clearing_prices = prices[indices]
      activity['Secondary']['electricity'] = - data * clearing_prices # want a cost in the end
    elif var.name == 'E_dump':
      activity['E_Penalty']['electricity'] = - data * 17000 # $/GW
    elif var.name == 'Stor':
      levels = store_initial - np.cumsum(data) * 3600
      activity['H2_storage']['H2'] = levels
  return activity

def opt_obj(stack, prices, loads, npp, grid, m):
  """ objective function for pyomo """
  # optimization variables -> use of storage, HTSE, secondary market
  ## costs:
  ##   -> secondary market for HTSE fixups -> SecMark * clearing_price[t]
  cost = 0
  for t in range(len(npp)):
    addl_e = m.SecM[t]
    # what clearing price?
    ## if we didn't change the clearing price, we can buy at price
    load = loads[t]
    new_load = load # FIXME + addl_e, except searchsorted fails for that!
    price_index = np.searchsorted(stack, new_load)
    new_price = prices[price_index]
    cost += addl_e * new_price * 1.1 # 10% markup for using secondary market
    ##   -> unused NPP -> 17 $/MW = 17000 $/GW for any unused electricity
    cost += m.E_dump[t] * 17000
  return cost

def opt_store(initial, store_cap, m, t):
  # 0 < stored < capacity
  lower = 0
  # m.Stor > 1 means producing, so we subtract the activity * dt
  var = initial - sum(m.Stor[i] for i in range(t+1))*3600
  high = store_cap
  return pyo.inequality(lower, var, high)

# def opt_avail(initial, market_cap, store_cap, m, t):
#   # available = initial + sum_0^t activity * dt
#   avail = initial + sum(m.Stor[i] for i in range(t+1))*3600
#   high = store_cap
#   return pyo.inequality(lower, var, high)

def debug_pyomo_print(m):
  print('/' + '='*80)
  print('DEBUGG model pieces:')
  print('  -> objective:')
  print('     ', m.objective.pprint())
  print('  -> variables:')
  for var in m.component_objects(pyo.Var):
    print('     ', var.pprint())
    print('  -> constraints:')
  for constr in m.component_objects(pyo.Constraint):
    print('     ', constr.pprint())
  print('\\' + '='*80)
  print('')

def debug_pyomo_soln(m):
  print('DEBUGG solution:')
  print('  -> objective:', m.objective())
  print('t: ' + ', '.join(f'{var.name:9s}' for var in m.component_objects(pyo.Var)))
  for t in m.T:
    msg = f'{t}: '
    for var in m.component_objects(pyo.Var):
      msg += f'{var[t].value:1.3e}, '
    print(msg)
  input()

def debug_setup_print(activity, m, stack, prices, comp_order, load,
                      htse_cap_h2, npp_cap, store_cap, store_initial, market_cap,
                      price_h2_kg, price_h2_GW, NPP_bid, H2_opp, bid_adjust):
  print('DEBUGG capacities:')
  print(f'  -> npp (GW): {npp_cap:1.2e}')
  print(f'  -> htse (kgH2/s): {htse_cap_h2:1.2e}')
  print(f'  -> store (kgH2): {store_cap:1.2e}')
  print(f'  -> store initial (kgH2): {store_initial:1.2e}')
  print(f'  -> market (kgH2/s): {market_cap:1.2e}')
  print('DEBUGG conversion/costs:')
  print(f'  -> HTSE e/H2 (GW/kg/s): {e_per_h2:1.2e}')
  print(f'  -> H2 price ($/kg/s): {price_h2_kg:1.2e}')
  print(f'  -> H2_opp ($/GW): {H2_opp:1.2e}')
  print(f'  -> NPP bid adjust ($/GW): {float(bid_adjust):1.2e}')
  print(f'  -> NPP TOTAL bid ($/GW): {float(NPP_bid):1.2e}')
  print('DEBUGG activity:')
  print('  t: load(GW), NPP->grid(GW)') #, htse(H2/s), store(H2)')
  template = '  {t}: {load:1.2e}, {grid:1.2e}' #, {htse:1.2e}, {store:1.2e}'
  for t in range(len(load)):
    print(template.format(t=t, load=load[t],
                          # npp=activity['NPP']['electricity'][t],
                          grid=activity['grid']['electricity'][t],
                          # htse=activity['HTSE']['H2'][t],
                          # store=activity['H2_storage']['H2'][t],
                          ))
  print('DEBUGG stack:')
  print('  i: stack, price, comp')
  for i in range(len(stack)):
    print(f'  {i}: {stack[i]:1.2e}, {prices[i]:1.2e}, {comp_order[i]}')