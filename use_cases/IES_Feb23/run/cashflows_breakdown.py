import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

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


def compute_cashflows(final_out):
  with open(final_out) as fp:
    lines = fp.readlines()
  dic = {}
  for c in CASHFLOWS:
    for l in lines:
      if ("CashFlow INFO (proj comp): Project Cashflow" in l) and (c in l) and ("amortize" not in l) and ("depreciate" not in l):
        ind = lines.index(l)
        if "capex" in c:
          avg_cashflow = float(lines[ind+2].split(" ")[-1])
          dic[c] = avg_cashflow
        else:
          values = []
          for i in range(3,23):
            values.append(float(lines[ind+i].split(" ")[-1]))
          avg_cashflow = sum(values)/len(values)
          dic[c] = [avg_cashflow]
  return dic




plants = ['braidwood', 'cooper', 'houston', 'prairie_island', 'stp', 'davis_besse']
CASHFLOWS = ['h2_storage_capex', 'diesel_sales','jet_fuel_sales','naphtha_sales','e_sales','elec_cap_market','co2_shipping'\
  'ft_vom','ft_fom','ft_capex','h2_ptc','htse_elec_cap_market','htse_vom','htse_fom','htse_capex'] #add rest later
df = pd.DataFrame(columns=['plant']+CASHFLOWS)
df.set_index('plant')

for plant in plants:
  final_out = find_final_out(plant)
  if final_out:
    dic = compute_cashflows(final_out)
    dic['plant'] = plant 
    temp_df = pd.DataFrame.from_dict(dic)
    df = pd.concat([df,temp_df], axis=0)
df.to_csv("./cashlow_breakdown.csv")



