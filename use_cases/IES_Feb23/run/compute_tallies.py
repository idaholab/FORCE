#!/usr/bin/env python
import argparse
import xml.etree.cElementTree as ET
from pathlib import Path
import json
import pandas as pd
import os, shutil
import matplotlib.pyplot as plt
import numpy as np

# Average densities for fuel products, from Wikipedia (kg/L)
FUEL_DENSITY = {'jet_fuel':0.8, 
                'diesel':0.85,
                'naphtha':0.77} # kg/L
GAL_to_L = 3.785 # L/gal

def parse_meta(xml_file):
  """ Parse the ROM meta xml file to get the cluster multiplicity information
  Returns a dictionary cluster_number:multiplicity"""
  root = ET.parse(xml_file).getroot()
  meta = {}
  for year_rom in root.findall("arma/MacroStepROM"):
      meta[int(year_rom.get('YEAR', '0'))] = {}
      for cluster in year_rom.findall("ClusterROM"):
          cluster_num = int(cluster.get('cluster', '999'))
          segments = tuple([int(i) for i in cluster.findtext('segments_represented').split(", ")])
          meta[int(year_rom.get('YEAR', '0'))][cluster_num] = [len(segments)]
  multiplicity_dic = dict(sorted(meta.items()))[0]
  return multiplicity_dic

def calculate_tallies(dispatch_file, rom_meta_xml, project_lifetime):
  """ 
  Compute the yearly tally for each dispatch variable 
    @ In, dispatch_file, str, path to the dispatch_print.csv file with the results of the debug dispatch run for a day
    @ In, mult_dic, dic, dictionary with cluster numbers as keys and corresponding multiplicity
    @ Out, ?
  """
  mult_dic = parse_meta(rom_meta_xml)
  dispatch = pd.read_csv(dispatch_file)
  # Clean up 
  toclean = ['RAVEN_sample_ID', 'scaling', 'price', 'prefix', 'hour']
  dispatch.drop(columns=toclean, inplace=True)
  for c in dispatch.columns:
    if "Probability" in str(c):
      dispatch.drop(columns=[c], inplace=True)
  # Sum over clusters and years
  dispatch = dispatch.groupby(['_ROM_Cluster', 'Year']).sum()
  # Multiplicity 
  mult = pd.DataFrame.from_dict(mult_dic).transpose()
  mult.rename({0:"multiplicity"}, axis=1, inplace=True)
  mult.index.names = ['_ROM_Cluster']
  new_dispatch = dispatch.join(mult, how="left")
  for c in new_dispatch.columns:
    if "Dispatch" in str(c):
      new_dispatch[c] = new_dispatch[c].multiply(new_dispatch['multiplicity'])
  new_dispatch.drop(columns=['multiplicity'], inplace=True)
  # Rename columns 
  new_dispatch.rename(lambda x: " ".join(x.split("__")[1:]).upper(), axis='columns', inplace=True)
  lifetime_tallies = new_dispatch.sum()
  #lifetime_tallies.to_csv("test_tallies.csv", header=None)
  return lifetime_tallies

def get_arma_path(heron_input_xml):
  """ 
  Parse the heron input file xml for the path to the ARMA file
    In, heron_input_xml, str, path to the heron input for the case
    Out, arma_xml, str, path to the ARMA file for the case
  """
  root = ET.parse(heron_input_xml).getroot()
  arma_xml = ''
  arma = root.find("DataGenerators/ARMA")
  path_arma_pk = arma.text
  output = path_arma_pk.split('/')[-2]
  arma_xml = os.path.join("train",output,"romMeta.xml")
  return arma_xml


def check_dispatch_run(case_folder, case_name):
  """ 
  Checks for the existence of a dispatch run results file in the gold or optimization folder
    @ In, case_folder, str, path to the case folder
    @ Out, dispatch_file, str, path to dispatch file or None if not there
  """
  if not os.path.isdir(case_folder):
    raise FileNotFoundError("The {} folder does not exist".format(case_folder))
  dispatch_file = None
  gold_file = os.path.join(case_folder, "gold", "dispatch_print.csv")
  o_file = os.path.join(case_folder, case_name+"_o", "dispatch_print.csv")
  if os.path.isfile(gold_file):
    dispatch_file = gold_file
  elif os.path.isfile(o_file):
    gold_dir = os.path.join(case_folder, "gold")
    if not os.path.exists(gold_dir):
        os.makedirs(gold_dir)
    shutil.copy2(o_file, gold_file)
    dispatch_file = gold_file
  return dispatch_file

def get_project_lifetime(heron_input_xml):
  """ Parse the heron input file xml for project lifetime 
    In, heron_input_xml, str, path to the heron input for the case
    Out, project_lifetime, float, project lifetime value"""
  root = ET.parse(heron_input_xml).getroot()
  project_lifetime = float(root.find("Case/economics/ProjectTime").text)
  return project_lifetime

def plot_lifetime_tallies(path_to_csv, save_path):
  """ 
  Plot lifetime tallies, electricity and synthetic fuel products
    @ In, path_to_csv, str, path to the csv file with the lifetime tallies
    @ Out, None 
  """
  df = path_to_csv.to_frame()
  elec_names =[]
  elec_values =[]
  synfuels_names =[]
  synfuels_values = []
  for c in df.index:
    if 'ELECTRICITY' in c and not('NPP' in c): 
      elec_names.append(c.split(' ')[0])
      elec_values.append(abs(df.loc[c][0]))
    if 'MARKET' in c and (('NAPHTHA' in c) or ('JET_FUEL' in c) or ('DIESEL' in c)):
      synfuels_names.append(c.split(' ')[-1])
      # kg to gal
      synfuels_values.append(abs(df.loc[c][0])*(1/GAL_to_L)*(1/FUEL_DENSITY[synfuels_names[-1].lower()])/1e6)
  fig, ax = plt.subplots(1,2, figsize=(10,6))
  def create_elec_labels(e_prod):
    labels = []
    for p in e_prod:
      l = str(int(np.round(p*100./np.sum(e_prod))))+' % \n'+str(np.round(p/1e6))+' TWh'
      labels.append(l)
    return labels
  labels = create_elec_labels(elec_values)
  wedges, texts = ax[1].pie(list(elec_values), labels = labels)
                                    #textprops=dict(color="w"))
  ax[1].legend(wedges, elec_names,bbox_to_anchor =(0.5,-0.2), loc='lower center')
  #ax[0].pie(elec.values(), labels=elec.keys())
  ax[0].bar(synfuels_names, synfuels_values)
  ax[0].set_ylabel("Production (Mgal)")
  ax[0].grid(axis='y')
  fig.tight_layout()
  fig.savefig(save_path)
  return None

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("location", type=str, help="Name of folder with case")
  args = parser.parse_args()
  
  #Check dispatch result file
  d = check_dispatch_run(os.path.join("./run", args.location), args.location)
  if d: 
    print("Dispatch results file found: {}".format(d))
  else: 
    print("Dispatch results file not found, exiting")
    exit()
  # Get ARMA location
  heron_input_xml = os.path.join("./run", args.location, "heron_input.xml")
  if not os.path.isfile(heron_input_xml):
    exit("Not heron input")
  else: 
    print("HERON input file found here: {}".format(heron_input_xml))
  rom_meta_xml = get_arma_path(heron_input_xml=heron_input_xml)
  # Get project lifetime
  project_lifetime = get_project_lifetime(heron_input_xml=heron_input_xml)
  # Compute tallies for the duration of the project
  print("Lifetime tallies: \n")
  lifetime_tallies = calculate_tallies(dispatch_file=d, rom_meta_xml=rom_meta_xml, project_lifetime=project_lifetime)
  print(lifetime_tallies)
  csv_path = os.path.join('./run', args.location, args.location+"_lifetime_tallies.csv")
  lifetime_tallies.to_csv(csv_path, header=None)
  fig_path = os.path.join('./run', args.location, args.location+"_lifetime_tallies_elec_synfuels.png")
  plot_lifetime_tallies(lifetime_tallies, fig_path)
  

if __name__ == '__main__':
  main()