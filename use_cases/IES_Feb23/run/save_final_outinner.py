import os, shutil
import pandas as pd
import argparse

def get_final_npv(plant):
  opt_out_file = os.path.join(".", plant, "gold","opt_soln_0.csv")
  sweep_file = os.path.join(".", plant, "gold", 'sweep.csv')
  opt_tag = True
  if os.path.isfile(opt_out_file):
    df = pd.read_csv(opt_out_file)
    final_npv = float(df.iloc[-1].loc['mean_NPV'])
    std_npv = float(df.iloc[-1].loc['std_NPV'])
  elif os.path.isfile(sweep_file):
    df = pd.read_csv(sweep_file)
    # ASSUME first line is the one to plot
    final_npv = float(df.iloc[0].loc['mean_NPV'])
    std_npv = float(df.iloc[0].loc['std_NPV'])
    opt_tag = False
  else: 
    raise FileNotFoundError("No sweep or optimization results in the gold folder of {} case".format(plant))
  return final_npv, std_npv, opt_tag

def find_final_out(plant):
  """Assumes this notebook is saved in run folder
  Function find_out_file(plant) returning the path to the right out~inner given the name of the plant
  Look for the right out~inner file
  For each out~inner file
  get all npv results, take the average and compare it to final results in opt_soln_0.csv
  if it is the right file save it to gold folder and save path to final_ou
  """
  plant_folder = "./"+plant
  final_npv, std_npv, opt_tag = get_final_npv(plant)
  for dirpath, dirnames, files in os.walk(plant_folder):
    for folder in dirnames: 
      if '_o' in folder:
        opt_folder = folder
  if opt_tag:
    opt_folder = os.path.join(plant_folder,opt_folder,"optimize")
  else: 
    opt_folder = os.path.join(plant_folder,opt_folder, "sweep" )
  # Get all the out~inner files path in a list
  out_files =[]
  for f in os.listdir(opt_folder):
    if not os.path.isfile(os.path.join(opt_folder,f)) and "_i" not in f:
      out_file = os.path.join(opt_folder,f, "out~inner")
      out_files.append(out_file)
  # Map each out~inner to corresponding NPV
  out_to_npv = {}
  for out_file in out_files:
      lines =[]
      with open(out_file, 'rb') as fp:
        for line in fp: 
          lines.append(line.decode(errors='ignore'))
      npvs = []
      for l in lines:
        if "   NPV" in l:
          npvs.append(float(l.split(" ")[-1]))
      if len(npvs) != 0:
        avg_npv = sum(npvs)/len(npvs)
        out_to_npv[out_file] = avg_npv
  final_out = False
  for out_file, npv in out_to_npv.items():
    if round(npv,1) == round(final_npv,1):
      final_out = out_file
  return final_out

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('case_name', type=str, help="Case folder name in the run directory")
  args = parser.parse_args()
  dir = os.path.dirname(os.path.abspath(__file__))
  case_folder = os.path.join(dir, args.case_name)
  final_out = find_final_out(args.case_name)
  if final_out: 
    print("Final out~inner found here: {}, \n and copied to gold, commit it!".format(final_out))
    shutil.copy(final_out, os.path.join(case_folder, "gold", "out~inner"))
  else: 
    print("Final out~inner file was not found, maybe the case has been re-run and the gold folder not updated?")



if __name__=="__main__":
 main()

