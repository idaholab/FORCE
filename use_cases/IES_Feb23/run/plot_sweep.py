import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

""" The goal of this script is to plot the results of a sweep run: a histogram plot with uncertainty
  and cases expressed in terms of HTSE, FT and H2 storage capacities"""


def plot_hist(plant_dir, case, sweep_df):
  # Compute 2x STD in a new column
  # Create new column with label "HTSE (MW), FT (ton-H2/h), h2 storage (ton-H2)"
  rename_dico = {'npp_capacity':'NPP (MW)',
                'htse_capacity':'HTSE (MW)',
                'ft_capacity': 'FT (ton-H2/h)',
                'h2_storage_capacity':'H2 Sto. (ton-H2)', 
                'delta_NPV':'Delta NPV ($M)',
                '2std_dNPV':'2STD Delta NPV ($M)'}
  sweep_df['ft_capacity'] = round(sweep_df['ft_capacity']/1000,1)
  sweep_df['delta_NPV'] = round(sweep_df['delta_NPV']/1e6,1)
  sweep_df['2std_dNPV'] = round(sweep_df['2std_dNPV']/1e6,1)
  sweep_df['h2_storage_capacity'] = round(sweep_df['h2_storage_capacity']/1000,1)
  sweep_df = sweep_df.rename(columns=rename_dico)
  print(sweep_df)
  # plot
  plt.style.use('ggplot')
  fig,ax = plt.subplots(2,1)
  sweep_df.plot(ax = ax[0], kind = "bar", y = 'Delta NPV ($M)', legend = False) 
  ax[0].errorbar(sweep_df.index, sweep_df['Delta NPV ($M)'],  yerr = sweep_df['2STD Delta NPV ($M)'], 
              linewidth = 1, color = "black", capsize = 2, fmt='none')
  ax[0].set_ylim(-1100,0)
  ax[0].set_ylabel('Delta NPV ($M)')
  # Overall
  #for key, spine in ax[0].spines.items():
   #   spine.set_visible(False)
  #ax[0].tick_params(bottom = False, left = False)
  
  ax[1].axis('tight')
  ax[1].axis('off')
  table_df = sweep_df.transpose()
  table = ax[1].table(cellText=table_df.values, 
                    colLabels=table_df.columns, 
                    rowLabels=table_df.index,
                    loc='upper right')
  fig.tight_layout()
  tosave = os.path.join(plant_dir,case+'_results.png' )
  fig.savefig(tosave)
  return None


def pp_sweep_results(sweep_file, mean_NPV_baseline, std_NPV_baseline):
  """
  Post processing of the sweep results: keep opt variables mean NPV and std NPV*2
  Sort values % mean NPV and keep the top 4:
    @ In, sweep_file, str, path to csv file results of sweep run
    @ In, mean_NPV_baseline, float, value for the mean NPV of the baseline (elec) case
    @ In, std_NPV_baseline, float, value for the std NPV of the baseline (elec) case
    @ Out, sweep_df, pd.DataFrame, sorted dataframe of results
  """
  s_df = pd.read_csv(sweep_file)
  sweep_df = pd.DataFrame()
  to_keep = ['npp_capacity','htse_capacity','ft_capacity', 'h2_storage_capacity', 'mean_NPV','std_NPV']
  for c in to_keep:
    sweep_df[c] = s_df[c]
  sweep_df['delta_NPV'] = sweep_df['mean_NPV']-mean_NPV_baseline
  sweep_df['2std_dNPV'] = 2*np.sqrt(np.power(sweep_df['std_NPV'],2)+np.power(std_NPV_baseline,2))
  sweep_df.sort_values(by=['mean_NPV'], ascending=False, inplace=True)
  sweep_df.reset_index(inplace=True)
  sweep_df.drop(columns=['index', 'std_NPV', 'mean_NPV'], inplace=True)
  sweep_df = sweep_df.iloc[:4,:]
  return sweep_df

def get_baseline_NPV(case):
  case_list = case.split("_")
  if ('ptc' in case_list) or ('om' in case_list) or ('capex' in case_list) or ('synfuels' in case_list) or ('co2' in case_list):
    baseline_case = case_list[0]+"_baseline"
  elif len(case_list)>1:
    baseline_case ="_".join(case_list[:-1])+"_baseline"
  else:
    baseline_case = case_list[0]+"_baseline"
  print("Baseline case :{}".format(baseline_case))
  baseline_file = os.path.join(baseline_case, 'gold', 'sweep.csv')
  if os.path.isfile(baseline_file):
    df = pd.read_csv(baseline_file)
    # Assume the right case is printed on the first line
    mean_NPV = float(df.iloc[0,:].mean_NPV)
    print('Baseline case mean NPV: {}'.format(mean_NPV))
    std_NPV = float(df.iloc[0,:].std_NPV)
    print('Baseline case std NPV: {}'.format(std_NPV))
  else:
    raise FileNotFoundError("Baseline results not found")
  return mean_NPV, std_NPV

def main():
  case = "braidwood_ptc_100"
  dir = os.path.dirname(os.path.abspath(__file__))
  os.chdir(dir)
  print("Current Directory: {}".format(os.getcwd()))
  plant_dir = os.path.join(dir, case)
  sweep_file = os.path.join(plant_dir, 'gold', 'sweep.csv')
  if os.path.isfile(sweep_file):
    mean_baseline, std_baseline = get_baseline_NPV(case)
    sweep_df = pp_sweep_results(sweep_file, mean_baseline, std_baseline)
    plot_hist(plant_dir, case, sweep_df)
  else:
    raise FileNotFoundError("Sweep results not found")

if __name__ == "__main__":
  main()