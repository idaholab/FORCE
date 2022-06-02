import math

coefs = { 'NOAK':{'m':1.294,
                  'f':1.382,
                  'a_sca':862.9, 
                  'n_sca':-0.501,
                  'a_mod':365.6,
                  'n_mod':0},
          'FOAK':{'m':1.294,
                  'f':1.382,
                  'a_sca':862.9, 
                  'n_sca':-0.501,
                  'a_mod':365.6,
                  'n_mod':0}}
AC_to_DC = 1/1.076 # AC power consumed over DC power consumed

def compute_capex(capacity, m,f,a_sca, n_sca, a_mod, n_mod):
  """ 
    Determines the capex of the HTSE plant in $/kW-AC
    @ In, capacity, float, capacity of the HTSE in MW-AC
    @ In, m, float, indirect cost multiplier
    @ In, f, float, installation factor
    @ In, a_sca, float, scalable equipment cost coefficient
    @ In, n_sca, float, scalable equipment scaling exponent
    @ In, a_mod, float, modular equipment cost coefficient
    @ In, n_mod, float, modular equipment scaling exponent
    @ Out, capex, float, capex in $/kW-AC
  """
  capex = m*f* ( a_sca*math.exp(n_sca*math.log(capacity*AC_to_DC)) + a_mod*math.exp(n_mod*math.log(capacity*AC_to_DC)))
  return capex

def htse_noak_capex(data, meta):
  """
    Determines the Capex cost of the HTSE plant (NOAK) in $/MW-AC
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  d = coefs['NOAK']
  m, f, a_sca, n_sca, a_mod, n_mod = d['m'], d['f'], d['a_sca'], d['n_sca'], d['a_mod'], d['n_mod']
  cap = math.fabs(meta['HERON']['RAVEN_vars']['htse_capacity']) # HTSE capacity cast as negative number
  capex = -1000*compute_capex(cap, m, f, a_sca, n_sca, a_mod, n_mod)
  data = {'driver': capex}
  return data, meta

if __name__ == "__main__":
  d = coefs['NOAK']
  m, f, a_sca, n_sca, a_mod, n_mod = d['m'], d['f'], d['a_sca'], d['n_sca'], d['a_mod'], d['n_mod']
  capex = -1000*compute_capex(250, m, f, a_sca, n_sca, a_mod, n_mod)
  print(capex)