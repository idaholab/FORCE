import math
import pandas as pd
import os, copy
import numpy as np

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

# Conversion coefficients for liquid fuel products
# https://www.bts.gov/content/energy-consumption-mode-transportation and 
# https://hextobinary.com/unit/energy/from/mmbtu/to/galnaphthaus
FUEL_CONV_MMBtu_GAL = {'jet_fuel':0.135, 
                      'diesel':0.1387, 
                      'naphtha':0.1269} # Gal/MMBtu
# Average densities for fuel products, from Wikipedia (kg/L)
FUEL_DENSITY = {'jet_fuel':0.8, 
                'diesel':0.85,
                'naphtha':0.77} # kg/L
GAL_to_L = 3.785 # L/gal
# To convert from $/MMBtu to $/kg: 
# $/kg  = $/MMBtu x FUEL_CONV_MMBtu_GAL x (1/GAL_to_L) x (1/FUEL_DENSITY)
# To get naphtha prices use scaling factor from gasoline price to naphtha based on current prices, dummy value for now
MG_to_N = 0.8026335 # Will Jenson data
HTSE_ELEC_to_H2 = 25.13 #kg-H2/MWe

def h2_ptc(data, meta):
  """
    Determines the PTC (Production Tax Credit) for hydrogen production : 
    PTC applicable only for the first 10 years of the simulation $3/kg-H2
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state information
  """
  year = meta['HERON']['active_index']['year'] # 0 to 29
  ptc = 0
  if year<10:
    ptc = 3 #$/kg-H2
  final_ptc = -HTSE_ELEC_to_H2*ptc #$/MWe
  data = {'reference_price':final_ptc}
  # driver is electricity: 25.13 kg-H2/MWe
  return data, meta

def diesel_credit(data, meta):
  """
  Determines the credits for diesel production: 
  credit only applicable for the first 10 years of the simulation
  $1.67/gal: $1.25/gal base credit plus $0.01/gal additional credit 
  for each percentage point reduction in the LCA carbon emissions 
  above 50% attributed to the synfuel; the ANL indicates a 92% carbon reduction 
  so $0.42/gal additional credit added to the base $1.25/gal
  """
  # Negative diesel activity for diesel market so credit should be negative to result in profit
  year = meta['HERON']['active_index']['year'] # 0 to 29
  credit = 0
  if year<10:
    credit = 1.67 #$/gal
  # Diesel activity in kg
  # Conversion
  credit = -credit*(1/GAL_to_L)*(1/FUEL_DENSITY['diesel']) #$/kg
  data = {'reference_price':credit}
  return data, meta

def jet_fuel_credit(data, meta):
  """
  Determines the credits for jet fuel production: 
  credit only applicable for the first 10 years of the simulation
  $1.67/gal: $1.25/gal base credit plus $0.01/gal additional credit 
  for each percentage point reduction in the LCA carbon emissions 
  above 50% attributed to the synfuel; the ANL indicates a 92% carbon reduction 
  so $0.42/gal additional credit added to the base $1.25/gal
  """
  # Negative diesel activity for diesel market so credit should be negative to result in profit
  year = meta['HERON']['active_index']['year'] # 0 to 29
  credit = 0
  if year<10:
    credit = 1.67 #$/gal
  # Diesel activity in kg
  # Conversion
  credit = -credit*(1/GAL_to_L)*(1/FUEL_DENSITY['jet_fuel']) #$/kg
  data = {'reference_price':credit}
  return data, meta

def get_syngas_capex(data, meta):
  """
    Determines the capex cost of the syngas storage
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state infomation
  """
  capacity_kg = meta['HERON']['RAVEN_vars']['syngas_storage_capacity']
  density = 0.95 #kg/m3
  cap = capacity_kg/density
  capex = cap*62.3+66223
  data = {'driver':capex}
  return data, meta

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

def htse_noak_capex_comb(data,meta):
  """
    Determines the Capex cost of the HTSE plant (NOAK) in $/MW-AC
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  d = coefs['NOAK']
  m, f, a_sca, n_sca, a_mod, n_mod = d['m'], d['f'], d['a_sca'], d['n_sca'], d['a_mod'], d['n_mod']
  cap = math.fabs(meta['HERON']['RAVEN_vars']['htse_ft_capacity']) # HTSE capacity cast as negative number
  capex = -1000*compute_capex(cap, m, f, a_sca, n_sca, a_mod, n_mod)
  data = {'driver': capex}
  return data, meta


def find_lower_nearest_idx(array, value): 
  idx = 0
  for i,a in enumerate(array):
    if value>a:
      idx = i
  return idx


def co2_supply_curve(data, meta):
  """
    Determines the cost of CO2 as a function of the quantity asked for, 
    Based on data from D. Wendt analysis on CO2 feedstock
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  co2_cost = 0
  ft_cap = meta['HERON']['RAVEN_vars']['ft_capacity'] #kg-H2
  h2_rate = 1.06
  co2_rate = 6.58
  co2_demand_year = 365*24*np.abs(ft_cap)*co2_rate/h2_rate #(kg/year)
  # Get the data for the NPP
  labels = meta['HERON']['Case'].get_labels()
  location = labels['location']
  location_path = '../data/'+str(location)+'_co2.csv'
  df = pd.read_csv(os.path.join(os.path.dirname(__file__), location_path))
  cost_data = df.iloc[:,-1].to_numpy()
  co2_demand_data = df.iloc[:,-2].to_numpy()
  diff = np.absolute(co2_demand_data-co2_demand_year)
  idx = np.argmin(diff)
  co2_cost = cost_data[idx]
  data = {'reference_price': -co2_cost}
  return data, meta 

def co2_suppy_curve_test(data, meta):
  """
    Determines the cost of CO2 as a function of the quantity asked for, 
    Based on data from D. Wendt analysis on CO2 feedstock
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  co2_cost = 0
  ft_cap = meta['HERON']['RAVEN_vars']['ft_capacity'] #kg-H2
  h2_rate = 1.06
  co2_rate = 6.58
  co2_demand_year = 365*24*np.abs(ft_cap)*co2_rate/h2_rate #(kg/year)
  # Get the data for the NPP
  labels = meta['HERON']['Case'].get_labels()
  location = labels['location']
  location_path = '../data/'+str(location)+'_co2.csv'
  df = pd.read_csv(os.path.join(os.path.dirname(__file__), location_path))
  cost_data = df.iloc[:,-1].to_numpy()
  co2_demand_data = df.iloc[:,-2].to_numpy()
  diff = np.absolute(co2_demand_data-co2_demand_year)
  idx = np.argmin(diff)
  co2_cost = cost_data[idx]
  data = {'reference_price': -co2_cost*co2_demand_year}
  return data, meta 

def co2_supply_curve_comb(data,meta):
  """
    Determines the cost of CO2 as a function of the quantity asked for, 
    For HTSE and FT combined component cases
    Based on data from D. Wendt analysis on CO2 feedstock
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  co2_cost = 0
  comp_cap = meta['HERON']['RAVEN_vars']['htse_ft_capacity'] #MWe (negative value)
  elec_to_h2_rate = 25.13 #kg-H2/MWe
  h2_to_co2_rate = 6.58/1.06 #kg-Co2/kg-h2
  comp_cap = np.abs(comp_cap)
  co2_demand_year = 365*24*comp_cap*elec_to_h2_rate*h2_to_co2_rate #(kg-CO2/year)
  # Get the data for the NPP
    # Get the data for the NPP
  labels = meta['HERON']['Case'].get_labels()
  location = labels['location']
  location_path = '../data/'+str(location)+'.csv'
  df = pd.read_csv(os.path.join(os.path.dirname(__file__), location_path))
  cost_data = df.iloc[:,-1].to_numpy()
  co2_demand_data = df.iloc[:,-2].to_numpy()
  diff = np.absolute(co2_demand_data-co2_demand_year)
  idx = np.argmin(diff)
  co2_cost = cost_data[idx]
  data = {'reference_price': -co2_cost}
  return data, meta

def co2_cost_low(data, meta):
  """
    Determines the yearly cost of the co2 feedstock for the FT process assuming a low price fo $1/ton
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  co2_cost = 0
  comp_cap = meta['HERON']['RAVEN_vars']['htse_ft_capacity'] #MWe (negative value)
  elec_to_h2_rate = 25.13 #kg-H2/MWe
  h2_to_co2_rate = 6.58/1.06 #kg-Co2/kg-h2
  co2_demand_year = 365*24*comp_cap*elec_to_h2_rate*h2_to_co2_rate #(kg-CO2/year)
  # Low price of $25/ton = $0.025/kg
  co2_price = 0.001 #$/kg
  co2_cost = co2_price*co2_demand_year
  data = {'driver': co2_cost} # Cost so negative value
  return data, meta

def co2_cost_high(data, meta):
  """
    Determines the yearly cost of the co2 feedstock for the FT process assuming a high price fo $75/ton
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ In, meta, dict, state information
  """
  co2_cost = 0
  comp_cap = meta['HERON']['RAVEN_vars']['htse_ft_capacity'] #MWe negative
  elec_to_h2_rate = 25.13 #kg-H2/MWe
  h2_to_co2_rate = 6.58/1.06 #kg-Co2/kg-h2
  co2_demand_year = 365*24*comp_cap*elec_to_h2_rate*h2_to_co2_rate #(kg-CO2/year) neg
  # High price of $75/ton = $0.075/kg
  co2_price = 0.075 #$/kg
  co2_cost = co2_price*co2_demand_year # neg
  data = {'driver': co2_cost} # Cost so negative value
  return data, meta


def jet_fuel_price(data, meta):
  """
    Determines the price of jet fuel given the year of the simulation
    for the EIA scenario indicated in the scenario label of the case
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state information
  """
  # Get the data about jet fuel prices
  path = os.path.join(os.path.dirname(__file__), '../data/regional_fuel_prices.csv')
  df = pd.read_csv(path, header=0)
  year = str(meta['HERON']['active_index']['year'] + 2020)
  # Get the price 
  labels = meta['HERON']['Case'].get_labels()
  region = str(labels['fuel_region'])
  scenario = str(labels['scenario'])
  #in $/gal
  priceGal = float(df.loc[((df['Product']=='jet_fuel') & (df['Location'] == region) & (df['Case'] == scenario))][year].values)
  price = priceGal*(1/GAL_to_L)*(1/FUEL_DENSITY['jet_fuel']) #in $/kg
  data = {'reference_price': price}
  return data, meta 

def naphtha_price(data, meta):
  """
    Determines the price of naphtha given the year of the simulation
    for the reference EIA scenario
    For now assuming the price of naphtha is proportional to the price of jet fuel
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state information
  """
  # Get the data about jet fuel prices
  # Using gasoline price projection and assuming naphtha prices are proportional
  # Get the data about jet fuel prices
  path = os.path.join(os.path.dirname(__file__), '../data/regional_fuel_prices.csv')
  df = pd.read_csv(path, header=0)
  year = str(meta['HERON']['active_index']['year'] + 2020)
  # Get the price 
  labels = meta['HERON']['Case'].get_labels()
  region = str(labels['fuel_region'])
  scenario = str(labels['scenario'])
  #in $/gal
  priceGal = float(df.loc[((df['Product']=='naphtha') & (df['Location'] == region) & (df['Case'] == scenario))][year].values)
  price = priceGal*(1/GAL_to_L)*(1/FUEL_DENSITY['naphtha']) #in $/kg
  data = {'reference_price': price}
  return data, meta  

def diesel_price(data, meta):
  """
    Determines the price of diesel given the year of the simulation
    for the reference EIA scenario
    @ In, data, dict, request for data
    @ In, meta, dict, state information
    @ Out, data, dict, filled data
    @ Out, meta, dict, state information
  """
  # Get the data about jet fuel prices
  path = os.path.join(os.path.dirname(__file__), '../data/regional_fuel_prices.csv')
  df = pd.read_csv(path, header=0)
  year = str(meta['HERON']['active_index']['year'] + 2020)
  # Get the price 
  labels = meta['HERON']['Case'].get_labels()
  region = str(labels['fuel_region'])
  scenario = str(labels['scenario'])
  #in $/gal
  priceGal = float(df.loc[((df['Product']=='diesel') & (df['Location'] == region) & (df['Case'] == scenario))][year].values)
  price = priceGal*(1/GAL_to_L)*(1/FUEL_DENSITY['diesel']) #in $/kg
  data = {'reference_price': price}
  return data, meta 

def test_capex():
  d = coefs['NOAK']
  m, f, a_sca, n_sca, a_mod, n_mod = d['m'], d['f'], d['a_sca'], d['n_sca'], d['a_mod'], d['n_mod']
  capex = -1000*compute_capex(250, m, f, a_sca, n_sca, a_mod, n_mod)
  print(capex)

def test_co2_supply_curve():
  meta = {'HERON':{'activity':{'co2':340000}}}
  data ={}
  data, meta = co2_supply_curve(data, meta)
  print(data['driver'])

if __name__ == "__main__":
  #test_co2_supply_curve()# Works!
  # Test jet fuel get price with reference EIA AEO
  meta = {'HERON':{'active_index':{'year':23}, 'Case':{''}}}
  data = {}
  data, meta = jet_fuel_price(data, meta)
  print(data['driver'])
