import pandas as pd 
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt

CASES = ['braidwood', 'cooper', 'davis_besse', 'prairie_island', 'stp']
CLUSTER_nb = 0
START_YEAR = 2018
STOP_YEAR = 2021

""" Script to plot a scatter plot Y=MWh to the grid, X=price of electricity ($/MWh), 
for each location a different color"""

def load_data(location):
  """ Get the data for given location: price and MWh to the grid"""
  path = os.path.join(location+"_dispatch", "gold", "dispatch_print.csv")
  if os.path.exists(path):
    df = pd.read_csv(path)
  else:
    raise FileExistsError("Dispatch results do not exist for the location {}".format(location))
  print("max price : {} ".format(max(df['price'])))
  df = df[(df['_ROM_Cluster']==CLUSTER_nb) & (df['Year']>=START_YEAR) &(df['Year']<=STOP_YEAR)]
  df_loc = df[['Year','price','Dispatch__electricity_market__production__electricity']]
  df_loc['location'] = location
  df_loc.rename(columns={'Dispatch__electricity_market__production__electricity':'electricity_market'},
                inplace=True)
  df_loc['electricity_market'] = np.abs(df_loc['electricity_market'])
  return df_loc

def aggregate_data(cases):
  list_df = []
  for case in cases: 
    list_df.append(load_data(case))
  df = pd.concat(list_df, axis=0, ignore_index=True)
  return df

def plot_dispatch_scatter(df):
  sns.set_theme(style='whitegrid')
  fig, ax = plt.subplots(1,2)
  g = sns.relplot( data=df, 
                    x="price", 
                    y='electricity_market', 
                    hue='location', 
                    style='location', 
                    col='Year', col_wrap=2)

  g.set_ylabels("Electricity sent to the grid (MWh)")
  g.set_xlabels("Electricity price ($/MWh)")
  g.tight_layout()
  fig_name = "scatter_dispatch_cluster_{}_years_{}_{}.png".format(CLUSTER_nb, START_YEAR, STOP_YEAR)
  g.savefig(fig_name)

def main():
  df = aggregate_data(cases=CASES)
  plot_dispatch_scatter(df)


def test():
  load_data('braidwood')

if __name__ == '__main__':
  main()