import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from cashflows_breakdown import get_final_npv, find_final_out, compute_cashflows

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
  df = pd.DataFrame(columns=['year'])
  df['year'] = [2020+i for i in range(21)]
  df.set_index(['year'], inplace=True)
  for c in CASHFLOWS: 
    list_rows =[]
    for l in lines:
      if ("CashFlow INFO (proj comp): Project Cashflow" in l) and (c in l) and ("amortize" not in l) and ("depreciate" not in l):
        ind = lines.index(l)
        for i in range(2,23):
          year = base_year+i-2
          value = float(lines[ind+i].split(" ")[-1])
          #print("Computing Cashflow {} for year {}: {}.".format(c,year, value))
          new_row = pd.DataFrame.from_dict({ 'year':[year], c:[value]})
          list_rows.append(new_row)
    df_c = pd.concat(list_rows, ignore_index=True)
    df_c.drop_duplicates(inplace=True)
    df_c.set_index(['year'], inplace=True)
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
    new_row = pd.DataFrame.from_dict({"year":[2020+i],"fcff":[fcff_list[i]]})
    list_rows.append(new_row)
  df = pd.concat(list_rows, ignore_index=True)
  df.set_index(['year'], inplace=True)
  return df

def compute_taxes(yearly_df, plant):
  min_year = min(yearly_df.index)
  max_year = max(yearly_df.index)
  list_rows = []
  for year in range(min_year, max_year+1):
    # Compute taxes as fcff - (revenues+costs)
    rc = 0
    for c in CASHFLOWS:
      c_value = yearly_df.at[year, c]
      rc += c_value
    fcff = yearly_df.at[year,'fcff']
    taxes = fcff -rc
    new_row = pd.DataFrame.from_dict({"year":[year],"tax":[taxes]})
    list_rows.append(new_row)
  df = pd.concat(list_rows, ignore_index=True)
  df.set_index(['year'], inplace=True)
  return df

def plot_yearly_cashflow(yearly_df, plant_dir, plant): 
  result_df = yearly_df.copy()
  # Combine for better visibility
  years = result_df.index
  # Compute total capex, o&m, elec cap market from more detailed costs
  result_df['capex'] = result_df['htse_capex']+result_df['ft_capex']+result_df['h2_storage_capex']
  result_df['om']=result_df['ft_vom']+result_df['ft_fom']+result_df['htse_vom']+result_df['htse_fom']+result_df['co2_shipping']
  result_df.drop(columns=['ft_vom', 'ft_fom', 'htse_vom', 'htse_fom', 'htse_capex', 'ft_capex','h2_storage_capex'], inplace=True)
  #result_df['elec_cap_market']=result_df['ft_elec_cap_market']+result_df['htse_elec_cap_market']
  #result_df.drop(columns=['ft_elec_cap_market', 'htse_elec_cap_market'], inplace=True)
  # TODO: take care of elec cap market later
  # Divide by 1e6 for results in M$ 
  for c in list(result_df.columns):
    if 'year' not in str(c):
      result_df[c] /=1e6
  # Rename columns 
  result_df.rename(lambda x: " ".join(x.split("_")).upper(), axis='columns', inplace=True)
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
    'HTSE ELEC CAP MARKET':'gold3',
    'TAX': 'firebrick', 
  }
  fig, ax = plt.subplots()
  #result_df.set_index(['year'], inplace=True)
  result_df.plot.bar(ax=ax, y=color_mapping.keys(), stacked=True)
  ax.set_ylabel('Cashflows (M$)')
  ax.yaxis.grid(which='major',color='gray', linestyle='dashed', alpha=0.7)
  plt.legend(ncol = 1, bbox_to_anchor=(1.05,1.0), frameon = False, loc="upper left")
  plt.gcf().set_size_inches(11, 6)
  plt.tight_layout()
  plt.subplots_adjust(bottom=0.1)
  plt.savefig(os.path.join(plant_dir, plant+"yearly_cashflow_breakdown.png"))

def plot_lifetime_cashflow(plant, final_out):
  final_npv, std_npv = get_final_npv(plant)
  final_dic = compute_cashflows(final_out, final_npv)
  result_df = pd.DataFrame.from_dict(final_dic)
  df = pd.DataFrame()
  df['category']
  print(result_df.transpose)
  # Compute total capex, o&m, elec cap market from more detailed costs
  result_df['capex'] = result_df['htse_capex']+result_df['ft_capex']+result_df['h2_storage_capex']
  result_df['om']=result_df['ft_vom']+result_df['ft_fom']+result_df['htse_vom']+result_df['htse_fom']+result_df['co2_shipping']
  result_df.drop(columns=['ft_vom', 'ft_fom', 'htse_vom', 'htse_fom', 'htse_capex', 'ft_capex','h2_storage_capex'], inplace=True)
  for c in list(result_df.columns):
      result_df[c] /=1e9
  result_df.rename(lambda x: " ".join(x.split("_")).upper(), axis='columns', inplace=True)
  fig, ax = plt.subplots()
  result_df.plot(ax=ax, kind="bar", bottom=final_npv/1e9,width=30)
  ax.set_ylabel('Revenues and cost bn$(2020)')
  ax.yaxis.grid(which='major',color='gray', linestyle='dashed', alpha=0.7)
  plt.xticks([])
  plt.tight_layout()
  plt.show()
  plt.close()
  pass

def plot_lifetime_cashflow_2(plant, final_out):
  final_npv, std_npv = get_final_npv(plant)
  final_dic = compute_cashflows(final_out, final_npv)
  result_df = pd.DataFrame.from_dict(final_dic)
  # Compute total capex, o&m, elec cap market from more detailed costs
  result_df['capex'] = result_df['htse_capex']+result_df['ft_capex']+result_df['h2_storage_capex']
  result_df['om']=result_df['ft_vom']+result_df['ft_fom']+result_df['htse_vom']+result_df['htse_fom']+result_df['co2_shipping']
  result_df.drop(columns=['ft_vom', 'ft_fom', 'htse_vom', 'htse_fom', 'htse_capex', 'ft_capex','h2_storage_capex'], inplace=True)
  # TRanspose for plotting
  df = result_df.transpose()
  df.reset_index(inplace=True)
  df.rename(columns={'index':'category', 0:'value'}, inplace=True)
  df['value'] = df['value'].div(1e6)
  # TODO rename categories with lambda x: " ".join(x.split("_")).upper()
  df['category'] = df['category'].apply(lambda x: " ".join(x.split("_")).upper())
  # calculate running totals
  y='value'
  x='category'
  df['tot'] = df[y].cumsum()
  df['tot1']=df['tot'].shift(1).fillna(0)
  # lower and upper points for the bar charts
  lower = df[['tot','tot1']].min(axis=1)
  upper = df[['tot','tot1']].max(axis=1)
  # mid-point for label position
  mid = (lower + upper)/2
  # positive number shows green, negative number shows red
  df.loc[df[y] >= 0, 'color'] = 'green'
  df.loc[df[y] < 0, 'color'] = 'red'
  # calculate connection points
  connect= df['tot1'].repeat(3).shift(-1)
  connect[1::3] = np.nan
  fig,ax = plt.subplots()
  # plot first bar with colors
  bars = ax.bar(x=df[x],height=upper, color =df['color'])
  # plot second bar - invisible
  plt.bar(x=df[x], height=lower,color='white')
  plt.ylabel('M$(USD)')
  # plot connectors
  plt.plot(connect.index,connect.values, 'k' )
  # plot bar labels
  for i, v in enumerate(upper):
      plt.text(i-.15, mid[i], f"{df[y][i]:,.0f}")
  # TODO rotate x ticks by45 degrees for better visibility
  plt.show()
  return None

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
    yearly = compute_yearly_cashflows(plant, final_out)
    yearly_df = fcff.join(yearly, how='left')
    taxes_df = compute_taxes(yearly_df, plant)
    yearly_df = yearly_df.join(taxes_df, how='left')
    yearly_df.to_csv(os.path.join(plant_dir, "yearly_cashflow.csv"))
    plot_lifetime_cashflow_2(plant,final_out)
    plot_yearly_cashflow(yearly_df, plant_dir=plant_dir, plant=plant)
  else:
    print("Final out was not found!!")
  #print("Current Directory: {}".format(os.getcwd()))