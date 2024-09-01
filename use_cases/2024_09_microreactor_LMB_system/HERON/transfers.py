
# Copyright 2024, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
  Implements transfer functions
"""
def fixedOM(data, meta):
  """
    return unit capacity
    @ In, data, dict, data requeset
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state information
  """
  c = float(meta['HERON']['RAVEN_vars']['LMB_capacity'])
  po = float(meta['HERON']['RAVEN_vars']['powerdummy_capacity'])
  du = c / po
  d = 1.36 * c**(-0.216)
  e = d
  data = {'reference_price': e}
  return data, meta

def energyocc(data, meta):
  """
    return unit capacity
    @ In, data, dict, data requeset
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state information
  """
  c = float(meta['HERON']['RAVEN_vars']['LMB_capacity'])
  d = 261.42 * c**(-0.04)
  e = d
  data = {'reference_price': e}
  return data, meta

def powerocc(data, meta):
  """
    return unit capacity
    @ In, data, dict, data requeset
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state information
  """
  c = float(meta['HERON']['RAVEN_vars']['powerdummy_capacity'])
  d = 130.13558 * c**(-0.093)
  e = d
  data = {'reference_price': e}
  return data, meta
