import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

plants = ['braidwood', 'cooper', 'prairie_island', 'stp', 'davis_besse'] # Add houston when converged
CASHFLOWS = ['h2_storage_capex', 'diesel_sales','jet_fuel_sales','naphtha_sales','e_sales','elec_cap_market','co2_shipping',\
  'ft_vom','ft_fom','ft_capex','h2_ptc','htse_elec_cap_market','htse_vom','htse_fom','htse_capex'] #add rest later

def get_final_npv(plant):
  opt_out_file = os.path.join(".", plant, "gold","opt_soln_0.csv")
  df = pd.read_csv(opt_out_file)
  final_npv = float(df.iloc[-1].loc['mean_NPV'])
  std_npv = float(df.iloc[-1].loc['std_NPV'])
  return final_npv, std_npv

def find_final_out(plant):
  """Assumes this notebook is saved in run folder
  Function find_out_file(plant) returning the path to the right out~inner given the name of the plant
  Look for the right out~inner file
  For each out~inner file
  get all npv results, take the average and compare it to final results in opt_soln_0.csv
  if it is the right file save it to gold folder and save path to final_ou
  """
  plant_folder = "./"+plant
  final_npv, std_npv = get_final_npv(plant)
  for dirpath, dirnames, files in os.walk(plant_folder):
    for folder in dirnames: 
      if '_o' in folder:
        opt_folder = folder
  opt_folder = os.path.join(plant_folder,opt_folder,"optimize")
  out_files =[]
  for f in os.listdir(opt_folder):
    if not os.path.isfile(os.path.join(opt_folder,f)) and "_i" not in f:
      out_file = os.path.join(opt_folder,f, "out~inner")
      out_files.append(out_file)
  out_to_npv ={}
  for out_file in out_files:
      with open(out_file) as fp:
        lines = fp.readlines()
      npvs = []
      for l in lines:
        if "   NPV" in l:
          npvs.append(float(l.split(" ")[-1]))
      if len(npvs) != 0:
        avg_npv = sum(npvs)/len(npvs)
        out_to_npv[out_file] = avg_npv
  final_out = False
  for out_file, npv in out_to_npv.items():
    if round(npv,2) == round(final_npv,2):
      final_out = out_file
  return final_out


def compute_cashflows(dir, plant, final_out):
  # Compute cashflows in optimization out file
  with open(final_out) as fp:
    lines = fp.readlines()
  dic = {}
  for c in CASHFLOWS:
    for l in lines:
      if ("CashFlow INFO (proj comp): Project Cashflow" in l) and (c in l) and ("amortize" not in l) and ("depreciate" not in l):
        ind = lines.index(l)
        values = []
        # Get value for each year and sum it up
        for i in range(2,23):
          values.append(float(lines[ind+i].split(" ")[-1]))
        dic[c] = [sum(values)]
  # Add the baseline npv to the dictionary
  base_sweep = pd.read_csv(os.path.join(dir,plant+'_baseline', 'gold', 'sweep.csv'))
  npvs = list(base_sweep['mean_NPV'])
  baseline_npv = min(npvs)
  dic['baseline_npv'] = -1*baseline_npv
  return dic

def plot_cashflows_3(dir, csv_file):
  result_df = pd.read_csv(csv_file)
  result_df = result_df.rename(columns={'elec_cap_market':'ft_elec_cap_market'})
  # Divide by 1e9 for results in bn$ and count baseline npv as cost
  for c in list(result_df.columns):
    if 'plant' not in str(c):
      result_df[c] /=1e9
    if 'baseline' in str(c):
      result_df[c] *=-1
  
  #Compute delta npv
  color_mapping ={
    'baseline_npv':'#104E8B',#CDC673
    'jet_fuel_sales':'#FFD700',
    'diesel_sales':'#FFAEB9',
    'naphtha_sales':'#FF6103',
    'h2_ptc':'#B8860B',#darkgoldenrod',
    'e_sales':'#B22222',#firebrick',
    'h2_storage_capex':'#98F5FF',#cadetblue1',
    'htse_capex':'#CDC673',#cadetblue2',
    'ft_capex':'#7AC5CD',#cadetblue3',
    'htse_fom':'#7FFF00',#chartreuse1',
    'htse_vom':'#458B00',#chartreuse4',
    'ft_fom':'#BF3EFF',#chartreuse3',
    'ft_vom':'#68228B',#chartreuse4',
    'htse_elec_cap_market':'#EEEEE0',#ivory2',
    'ft_elec_cap_market':'#8B8B83'#ivory4'
  }

  fig = plt.figure(figsize=(80, 50))
  # Stacked bars for cashflows
  ax = fig.add_subplot(111)
  ax_bar = result_df.plot.bar(stacked=True,\
    color=[color_mapping.get(x, '#333333') for x in result_df.columns])
  legend_labels = [" ".join(l.split("_")).upper() for l in list(result_df.columns)]
  # x ticks
  plants_names = [" ".join(p.split('_')).upper() for p in plants]
  ax.set_axisbelow(True)
  ax.set_ylabel('Revenues and cost bn$(2020)')
  ax.yaxis.grid(color='gray', linestyle='dashed', alpha=0.7)
  ax.set_xticklabels(labels = plants_names, rotation=0)
  # Add annotation to indicate delta npv
  dnpv_df = pd.DataFrame()
  dnpv_df['delta_npv'] = result_df.sum(axis=1)  
  print(dnpv_df)
  #ax_bar.bar_label(ax.containers(),labels=dnpv_df['delta_npv'],label_type='center')
  #ax2 = ax.twinx()
  #ax2.plot(dnpv_df.index, dnpv_df['delta_npv'], 'rD')
  plt.legend(legend_labels, ncol = 1, bbox_to_anchor=(1.05,1.0), frameon = False, loc="upper left")
  plt.gcf().set_size_inches(10, 6)
  plt.tight_layout()
  plt.savefig(dir+'/cashflow_breakdown.png')

def plot_cashflows_2(dir, csv_file):
  result_df = pd.read_csv(csv_file)
  result_df = result_df.rename(columns={'elec_cap_market':'ft_elec_cap_market'})
  # Divide by 1e9 for results in bn$ and count baseline npv as cost
  for c in list(result_df.columns):
    if 'plant' not in str(c):
      result_df[c] /=1e9
    #if 'baseline' in str(c):
     # result_df[c] *=-1
  print(result_df)
  #Compute delta npv
  color_mapping ={
    'baseline_npv':'#104E8B',#CDC673
    'jet_fuel_sales':'#FFD700',
    'diesel_sales':'#FFAEB9',
    'naphtha_sales':'#FF6103',
    'h2_ptc':'#B8860B',#darkgoldenrod',
    'e_sales':'#B22222',#firebrick',
    'h2_storage_capex':'#98F5FF',#cadetblue1',
    'htse_capex':'#CDC673',#cadetblue2',
    'ft_capex':'#7AC5CD',#cadetblue3',
    'htse_fom':'#7FFF00',#chartreuse1',
    'htse_vom':'#458B00',#chartreuse4',
    'ft_fom':'#BF3EFF',#chartreuse3',
    'ft_vom':'#68228B',#chartreuse4',
    'htse_elec_cap_market':'#EEEEE0',#ivory2',
    'ft_elec_cap_market':'#8B8B83'#ivory4'
  }

  fig, ax = plt.subplots()
  # Stacked bars for cashflows
  ax = result_df.plot.bar(stacked=True,\
    color=[color_mapping.get(x, '#333333') for x in result_df.columns])
  legend_labels = [" ".join(l.split("_")).upper() for l in list(result_df.columns)]
  # x ticks
  plants_names = [" ".join(p.split('_')).upper() for p in plants]
  ax.set_axisbelow(True)
  ax.set_ylabel('Revenues and cost bn$(2020)')
  ax.yaxis.grid(color='gray', linestyle='dashed', alpha=0.7)
  ax.set_xticklabels(labels = plants_names, rotation=0)
  # Add table below to indicate delta npv
  delta_npvs = list(result_df.sum(axis=1)) 
  delta_npvs = [str(round(d,3)) for d in delta_npvs]
  delta_npvs = [delta_npvs]
  col_labels =[' ' for p in plants_names]
  plt.table(cellText=delta_npvs,cellLoc='center', loc ='bottom',rowLabels=[r'$\Delta$ NPV (bn\$(2020))'], colLabels=col_labels)
  plt.legend(legend_labels, ncol = 1, bbox_to_anchor=(1.05,1.0), frameon = False, loc="upper left")
  plt.gcf().set_size_inches(11, 6)
  plt.tight_layout()
  plt.subplots_adjust(bottom=0.1)
  plt.savefig(dir+'/cashflow_breakdown.png')

def create_cashflow_csv(dir):
  df = pd.DataFrame(columns=['plant']+CASHFLOWS)
  df.set_index('plant')

  for plant in plants:
    final_out = find_final_out(plant)
    if final_out:
      dic = compute_cashflows(dir, plant, final_out)
      dic['plant'] = plant 
      temp_df = pd.DataFrame.from_dict(dic)
      df = pd.concat([df,temp_df], axis=0)
  df.to_csv("./cashflow_breakdown.csv",index=False)

if __name__=="__main__":
  dir = os.path.dirname(os.path.abspath(__file__))
  create_cashflow_csv(dir)
  plot_cashflows_2(dir,dir+"/cashflow_breakdown.csv")



