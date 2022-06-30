"""
Custom Dispatcher for 2022 Synfuel project studying the economical feasibility of an IES 
producing both electricity and synthetic fuel products
"""
from functools import partial
import numpy as np
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

STO_TECHS = ['h2_storage']
PROD_TECHS = ['htse', 'ft']
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
            'resource': components[name].get_interaction().get_resource(),
            'capacity': components[name].get_capacity(info)[0][components[name].get_interaction().get_resource()],
            'component': components[name],
            'RTE': float(components[name].get_sqrt_RTE())
        }) for name in STO_TECHS)

    # Producers data
    prod_data = dict(
        (name, {
            'capacity_lower': components[name].get_capacity(info)[0][components[name].get_interaction().get_resource()],
            'capacity_upper': components[name].get_capacity(info)[1][components[name].get_interaction().get_resource()],
            'component': components[name]
        }) for name in PROD_TECHS
    )

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
                    bounds=(prod_data['htse']['capacity_lower'], prod_data['htse']['capacity_lower'])) #TODO: check this really reads capacity bounds
    m.FTElecConsumption = -14.9
    m.FT = pyo.Var(m.T, 
                   within=pyo.NonPositiveReals,
                   bounds=(prod_data['ft']['capacity_lower'], prod_data['ft']['capacity_lower'])) #TODO: check this really reads capacity bounds

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
    
    # Conservation Constraints Functions
    # Electricity
    m.EConserve = pyo.Constraint(m.T, rule=_conserve_elec)
    # Hydrogen 
    m.H2Conserve = pyo.Constraint(m.T, rule=_conserve_h2)

    # Transfer Functions for storage
    for tech in STO_TECHS:
        func = partial(_storage_mgmt_level, tech)
        setattr(m, f'{tech}_mgmt_level', pyo.Constraint(m.T, rule=func))

    # Objective function
    m.Obj = pyo.Objective(sense=pyo.maximize, rule=_objective)

    # Print and solve
    m.pprint()
    soln = pyo.SolverFactory('ipopt').solve(m)
    if soln.solver.status == SolverStatus.ok and soln.solver.termination_condition == TerminationCondition.optimal:
        print('Successful optimization solve.')
        debug_pyomo_soln(m)
    else:
        print('Storage optimization FAILURE!')
        print(' ... status:', soln.solver.status)
        print(' ... termination:', soln.solver.termination_condition)
        m.pprint()
        raise RuntimeError('Failed solve!')

    # Set components activity
    # Storage
    for stotech in STO_TECHS: 
        for trackr in ['level', 'charge', 'discharge']: 
            act = np.array(list(getattr(m, f'{stotech}_{trackr}')[t].value for t in m.T))
            activity_matrix.set_activity_vector(
                components[stotech], 
                storage_dat[stotech]['resource'],
                act,
                tracker = trackr
            )
    # HTSE
    htse_elec = np.array(list(m.HTSE[t].value for t in m.T))
    activity_matrix.set_activity_vector(components['htse'], 'electricity', htse_elec)
    # FT
    ft_h2 = np.array(list(m.FT[t].value for t in m.T))
    activity_matrix.set_activity_vector(components['ft'], 'h2', ft_h2)

    return activity_matrix




def _objective(m):
    # TODO write this
    pass


def _conserve_elec(m,t):
    # TODO write this
    pass


def _conserve_h2(m,t):
    # TODO write this
    pass

def _storage_mgmt_level(name, m, t):
    """
    TODO
    """
    level = getattr(m, f'{name}_level')
    charge = getattr(m, f'{name}_charge')
    discharge = getattr(m, f'{name}_discharge')
    if t > 0:
        prev = level[t-1]
    else:
        prev = m.StorageDat[name]['initial_level']
    sqrt_rte = m.StorageDat[name]['RTE']
    prod = (-sqrt_rte * charge[t]) - (discharge[t] / sqrt_rte)
    # we multiply by dt here but it's 1 always
    return level[t] == prev + prod * 1

def debug_pyomo_soln(m):
    print('DEBUGG solution:')
    print('  -> objective:', m.OBJ())
    print('t: ' + ', '.join(f'{var.name:9s}' for var in m.component_objects(pyo.Var)))
    for t in m.T:
        msg = f'{t}: '
        for var in m.component_objects(pyo.Var):
            msg += f'{var[t].value:1.3e}, '
            print(msg)