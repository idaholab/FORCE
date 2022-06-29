"""
Custom Dispatcher for 2022 Synfuel project studying the economical feasibility of an IES 
producing both electricity and synthetic fuel products
"""
from functools import partial
import numpy as np
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

STO_TECHS = ['h2_storage']
# To implement: 
# - Objective function: Elec, jet fuel, naphtha, diesel revenues minus all capex, fom, vom, elec cap costs
# - Constraints: 
#   - Fixed turbine production
#   - HTSE: 
#       - independent dispatch
#   - FT: 
#       - Fixed electricity consumption
#       - Fixed dispatch
#   - Markets: act as sinks taking whatever is left from one resource
#   - H2 storage: 
#       - independent dispathc
#       - specific to storage level, charge, discharge, RTE

def dispatch(info, activity_matrix): 
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

    # Get electricity prices for the day
    elec_price = heron['RAVEN_vars']['price']
    # Get length from ARMA
    time_dt = 1
    T = len(elec_price)

    # H2 storage data
    storage_dat =  dict(
        (name, {
            'initial_level': float(components[name].get_interaction().get_initial_level(info)),
            'capacity': components[name].get_capacity(info)[0][components[name].get_interaction().get_resource()],
            'component': components[name],
            'RTE': float(components[name].get_sqrt_RTE())
        }) for name in STO_TECHS)

    ## PYOMO Model ###
    m = pyo.ConcreteModel()
    Ts = np.arange(0,T, dtype=int)
    m.T = pyo.Set(initialize=Ts)
    m.elecPrice = elec_price
    m.storageDat = storage_dat

    # Fixed turbine capacity
    m.turbineCap = 1000 #TODO create case dict later with micro, SMR and no storage options

    # HTSE, FT, Storage capacities
    m.HTSE = pyo.Var(m.T,
                    within=pyo.NonPositiveReals,
                    bounds=())
    m.FTElecConsumption = -14.9

    # Storage
    # Create 3 pyomo vars for each TES
    for tes in STO_TECHS:
        cap = storage_dat[tes]['capacity']
        level = pyo.Var(m.T,
                        within=pyo.NonNegativeReals,
                        bounds=(0, cap),
                        initialize=0)
        charge = pyo.Var(m.T,
                         within=pyo.NonPositiveReals,
                         bounds=(-cap/time_dt, 0),
                         initialize=0)
        discharge = pyo.Var(m.T,
                            within=pyo.NonNegativeReals,
                            bounds=(0, cap/time_dt),
                            initialize=0)
        setattr(m, f'{tes}_level', level)
        setattr(m, f'{tes}_charge', charge)
        setattr(m, f'{tes}_discharge', discharge)

