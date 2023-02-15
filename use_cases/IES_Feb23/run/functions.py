import math
import pandas as pd
import os, copy
import numpy as np

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
  data = {'reference_price': -co2_cost*co2_demand_year}
  return data, meta 

def co2_supply_curve_test(data, meta):
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


if __name__ == "__main__":
  #test_co2_supply_curve()# Works!
  # Test jet fuel get price with reference EIA AEO
  meta = {'HERON':{'active_index':{'year':23}, 'Case':{''}}}
  data = {}
  data, meta = jet_fuel_price(data, meta)
  print(data['driver'])
