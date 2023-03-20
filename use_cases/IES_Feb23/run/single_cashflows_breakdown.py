import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from cashflows_breakdown import get_final_npv, find_final_out, compute_cashflows

""" The goal of this script is to produce a csv and png files showing the yearly and total 
    cashflows breakdown for a given NPP"""

CASHFLOWS = ['h2_storage_capex', 'diesel_sales','jet_fuel_sales','naphtha_sales','e_sales'\
            ,'co2_shipping','ft_vom','ft_fom','ft_capex','h2_ptc','htse_elec_cap_market','htse_vom','htse_fom','htse_capex'] #cahnge elec_cap_market to ft_elec_cap_market and add it TODO

DISCOUNT_RATE = 0.1 #10% used 

def get_yearly_cashflows(plant, final_out):
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
  }
  fig, ax = plt.subplots()
  #result_df.set_index(['year'], inplace=True)
  result_df.plot.bar(ax=ax, y=color_mapping.keys(), stacked=True)
  ax.set_ylabel('Cashflows (M$(2020))')
  ax.yaxis.grid(which='major',color='gray', linestyle='dashed', alpha=0.7)
  plt.legend(ncol = 1, bbox_to_anchor=(1.05,1.0), frameon = False, loc="upper left")
  plt.gcf().set_size_inches(11, 6)
  plt.tight_layout()
  plt.subplots_adjust(bottom=0.1)
  plt.savefig(os.path.join(plant_dir, plant+"_yearly_cashflow_breakdown.png"))

def plot_lifetime_cashflow(plant, plant_dir, lifetime_df):
  result_df = lifetime_df.copy()
  npv = result_df['npv']
  result_df.drop(columns={'npv'}, inplace=True)
  print(npv.to_numpy())
  # Compute total capex, o&m, elec cap market from more detailed costs
  try: 
    result_df['capex'] = result_df['htse_capex']+result_df['ft_capex']+result_df['h2_storage_capex']
    result_df.drop(columns=['htse_capex', 'ft_capex','h2_storage_capex'], inplace=True)
  except KeyError: 
    result_df['capex'] = result_df['htse_capex']+result_df['ft_capex']
    result_df.drop(columns=['htse_capex', 'ft_capex'], inplace=True)
  result_df['om']=result_df['ft_vom']+result_df['ft_fom']+result_df['htse_vom']+result_df['htse_fom']+result_df['co2_shipping']
  result_df.drop(columns=['ft_vom', 'ft_fom', 'htse_vom', 'htse_fom'], inplace=True)
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
  ax.yaxis.grid(which='major',color='gray', linestyle='dashed', alpha=0.7)
  # plot second bar - invisible
  plt.bar(x=df[x], height=lower,color='white')
  plt.ylabel('M$(2020(USD))')
  # plot connectors
  plt.plot(connect.index,connect.values, 'k' )
  # plot bar labels
  for i, v in enumerate(upper):
      plt.text(i-.15, mid[i], f"{df[y][i]:,.0f}")
  plt.xticks(rotation=90)
  plt.gcf().set_size_inches(11, 6)
  plt.tight_layout()
  plt.savefig(os.path.join(plant_dir, plant+"_total_cashflow_breakdown.png"))
  return None

def discount_yearly_cashflow(yearly_df, discount_rate):
  """ Discount the values for the yearly cashflows i.e. divide by (1+r)^y
    @ In, yearly_df, pd.DataFrame, dataframe with cashflow (columns) values per year (rows)
    @ Out, new_df, pd.DataFrame, dataframe with discounted cashflow (columns) values per year (rows)
  """
  yearly_df.reset_index(inplace=True)
  base_year = yearly_df['year'].min()
  new_df = pd.DataFrame()
  new_df['year'] = yearly_df['year']
  for c in yearly_df.columns: 
    if 'year' not in c:
      new_df[c] = yearly_df[c]/(np.power(1+discount_rate,yearly_df.index))
  return new_df

def create_final_cashflows(yearly_df):
  """
  From the discounted yearly cashflows create the lifetime total cashflow dataframe
    @ In, yearly_df, pd.DataFrame, dataframe containing the yearly discounted cashflows
    @ Out, lifetime_df, pd.DataFrame, dataframe with the total lifetime cashflows
  """
  new = yearly_df.drop(columns={'year'}).rename(columns={'fcff':'npv'})
  lifetime_df = new.sum().to_frame().transpose()
  return lifetime_df


def test(plant, final_out, plant_dir, total=True): 
  fcff = get_yearly_fcff(plant,final_out)
  yearly = get_yearly_cashflows(plant, final_out)
  yearly_df = fcff.join(yearly, how='left')
  yearly_df = discount_yearly_cashflow(yearly_df, DISCOUNT_RATE)
  yearly_df.to_csv(os.path.join(plant_dir, plant+"_yearly_cashflow.csv"))
  lifetime_df = create_final_cashflows(yearly_df)
  lifetime_df.to_csv(os.path.join(plant_dir, plant+"_total_cashflows.csv"))
  plot_yearly_cashflow(yearly_df, plant_dir=plant_dir, plant=plant)
  plot_lifetime_cashflow(plant, plant_dir,lifetime_df)

def main(plant, final_out, plant_dir, total=True):
  if total: 
    plot_lifetime_cashflow(plant,plant_dir,final_out)
  else:
    fcff = get_yearly_fcff(plant,final_out)
    yearly = get_yearly_cashflows(plant, final_out) 
    yearly_df = fcff.join(yearly, how='left')
    yearly_df.to_csv(os.path.join(plant_dir, "yearly_cashflow.csv"))
    plot_yearly_cashflow(yearly_df, plant_dir=plant_dir, plant=plant)


if __name__ == "__main__":
  dir = os.path.dirname(os.path.abspath(__file__))
  os.chdir(dir)
  print("Current Directory: {}".format(os.getcwd()))
  plant = "cooper"
  plant_dir = os.path.join(dir,plant)
  #final_out = find_final_out(plant)
  # For now until results are updated TODO update
  final_out = "braidwood_baseline_synfuel/gold/out~inner"
  final_out = "cooper/gold/out~inner"
  if final_out:
    print("Final out was found here: {}".format(final_out))
    #main(plant, final_out=final_out, plant_dir=plant_dir, total=True)
    test(plant, final_out, plant_dir)
  else:
    print("Final out was not found!!")