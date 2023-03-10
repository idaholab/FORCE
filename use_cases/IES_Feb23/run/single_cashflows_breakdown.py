import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from cashflows_breakdown import get_final_npv, find_final_out

""" The goal of this script is to produce a csv and png files showing the yearly and total 
    cashflows breakdown for a given NPP"""

CASHFLOWS = ['h2_storage_capex', 'diesel_sales','jet_fuel_sales','naphtha_sales','e_sales'\
            ,'co2_shipping','ft_vom','ft_fom','ft_capex','h2_ptc','htse_elec_cap_market','htse_vom','htse_fom','htse_capex'] #cahnge elec_cap_market to ft_elec_cap_market and add it TODO

plant = "cooper"

def compute_yearly_cashflows(plant, final_out):
  with open(final_out) as fp:
    lines = fp.readlines()
  npv = 0.0
  base_year = 2020
  df = pd.DataFrame(columns=['plant', 'year'])
  df['year'] = [2020+i for i in range(21)]
  df['plant'] = 'cooper'
  df.set_index(['plant', 'year'], inplace=True)
  for c in CASHFLOWS: 
    list_rows =[]
    for l in lines:
      if ("CashFlow INFO (proj comp): Project Cashflow" in l) and (c in l) and ("amortize" not in l) and ("depreciate" not in l):
        ind = lines.index(l)
        for i in range(2,23):
          year = base_year+i-2
          value = float(lines[ind+i].split(" ")[-1])
          #print("Computing Cashflow {} for year {}: {}.".format(c,year, value))
          new_row = pd.DataFrame.from_dict({'plant':[plant], 
                                            'year':[year], 
                                            c:[value]})
          list_rows.append(new_row)
    df_c = pd.concat(list_rows, ignore_index=True)
    df_c.drop_duplicates(inplace=True)
    df_c.set_index(['plant', 'year'], inplace=True)
    df = df.join(df_c, how='left')
  return df

def get_yearly_fcff(plant, final_out):
  with open(final_out) as fp:
    lines = fp.readlines()
  list_rows = []
  for l in lines: 
    if ("CashFlow INFO (FCFF): FCFF yearly (not discounted):" in l):
      ind = lines.index(l)
      # Get the next 6 lines
      to_split = ""
      for i in range(1,7):
        to_split+=lines[ind+i]
      # Remove first and last characters
      to_split = to_split[2:-2]
      fcff_list = to_split.split("   ")
      fcff_list = [float(f) for f in fcff_list]
  for i in range(len(fcff_list)):
    new_row = pd.DataFrame.from_dict({"plant":[plant],
              "year":[2020+i],
              "fcff":[fcff_list[i]]})
    list_rows.append(new_row)
  df = pd.concat(list_rows, ignore_index=True)
  return df

def compute_taxes(yearly_df, plant):
  min_year = min(yearly_df['year'])
  max_year = max(yearly_df['year'])
  list_rows = []
  for year in range(min_year, max_year+1):
    # Compute taxes as fcff - (revenues+costs)
    rc = 0
    for c in CASHFLOWS:
      # TODO update
      c_df = yearly_df[(yearly_df['cashflow']==c) & (yearly_df['year']==year)]['value'].mean()# # values = # arma samples
      rc+= c_df
    fcff = yearly_df[(yearly_df['year']==year)& (yearly_df['cashflow']=='fcff')]['value']
    fcff = float(fcff)
    taxes = fcff -rc
    new_row = pd.DataFrame.from_dict({"plant":[plant],
                "year":[year],
                "tax":[taxes]
                })
    list_rows.append(new_row)
  df = pd.concat(list_rows, ignore_index=True)
  return df

def plot_yearly_cashflow(yearly_df, plant_dir, plant): 
  result_df = yearly_df[['year', 'cashflow','value']]
  # Combine for better visibility
  years = result_df['year'].unique()
  # Compute total capex, o&m, elec cap market from more detailed costs
  capex_list = ['ft_capex', 'htse_capex', 'h2_storage_capex']
  om_list = ['ft_vom', 'ft_fom', 'htse_vom', 'htse_fom']
  elec_cap_market_list = ['ft_elec_cap_market', 'htse_elec_cap_market']
  final_list =['om', 'capex', 'elec_cap_market', 'co2_shipping', 'diesel_sales', 'jet_fuel_sales', 'e_sales',\
              'h2_ptc', 'naphtha_sales', 'tax']
  for year in years: 
    year_df = result_df[result_df['year']==year]
    # CAPEX
    capex = year_df[year_df['cashflow'].isin(capex_list)].sum()['value']
    capex_df = pd.DataFrame.from_dict({'year':[year],
                                        'cashflow':['capex'],
                                        'value':[capex]})
    # OM 
    om = year_df[year_df['cashflow'].isin(om_list)].sum()['value']
    om_df = pd.DataFrame.from_dict({'year':[year],
                                    'cashflow':['om'],
                                    'value':[om]})
    # Elec cap market
    elec_cap_market = year_df[year_df['cashflow'].isin(elec_cap_market_list)].sum()['value']
    elec_cap_market_df = pd.DataFrame.from_dict({'year':[year],
                                    'cashflow':['elec_cap_market'],
                                    'value':[elec_cap_market]})
    # Add new data to results
    result_df = pd.concat([result_df, capex_df, om_df, elec_cap_market_df], ignore_index=True)
  # Get rid of some entries
  result_df = result_df[result_df['cashflow'].isin(final_list)]
  # Divide by 1e6 for results in M$ 
  result_df['value'] /=1e6
  # Rename columns 
  result_df['cashflow'].apply(lambda x: " ".join(x.split("_")).upper())
  # Colors
  color_mapping ={
    'JET FUEL SALES':'blue',
    'DIESEL SALES':'green',
    'NAPHTHA SALES':'yellow',
    'H2 PTC':'pink',
    'E SALES':'black',
    'CAPEX':'orange',
    'OM':'cornsilk1',
    'CO2 SHIPPING':'chartreuse1',
    'ELEC CAP MARKET':'gold3',
    'TAXES': 'firebrick', 
  }
  fig, ax = plt.subplots()
  result_df.plot.bar(ax=ax, x='year', y=color_mapping.keys(), stacked=True)
  ax.set_ylabel('Cashflows (M$)')
  ax.yaxis.grid(which='major',color='gray', linestyle='dashed', alpha=0.7)
  plt.legend(ncol = 1, bbox_to_anchor=(1.05,1.0), frameon = False, loc="upper left")
  plt.gcf().set_size_inches(11, 6)
  plt.tight_layout()
  plt.subplots_adjust(bottom=0.1)
  plt.savefig(os.path.join(plant_dir, plant+"yearly_cashflow_breakdown.png"))


if __name__ == "__main__":
  dir = os.path.dirname(os.path.abspath(__file__))
  os.chdir(dir)
  print("Current Directory: {}".format(os.getcwd()))
  plant_dir = os.path.join(dir,plant)
  #final_out = find_final_out(plant)
  # For now until results are updated TODO update
  final_out = "cooper/cooper_o/optimize/1/out~inner"
  if final_out:
    print("Final out was found here: {}".format(final_out))
    fcff = get_yearly_fcff(plant,final_out)
    print(fcff.head())
    yearly = compute_yearly_cashflows(plant, final_out)
    print(yearly.head())
    yearly_df = pd.merge(fcff, yearly,left_on=['plant', 'year'], right_on=['plant', 'year'])
    #yearly_df.drop_duplicates(inplace=True)
    #taxes_df = compute_taxes(yearly_df, plant)
    #yearly_df = pd.concat([yearly_df,taxes_df],ignore_index=True)
    #yearly_df = yearly_df.groupby(['plant','year','cashflow']).mean()
    #yearly_df.to_csv(os.path.join(plant_dir, "yearly_cashflow.csv"))
    print(yearly_df)
    #plot_yearly_cashflow(yearly_df.reset_index(), plant_dir=plant_dir, plant=plant)
  else:
    print("Final out was not found!!")
  #print("Current Directory: {}".format(os.getcwd()))