# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
The objective of this code is the vertical integration (auomated data transfer) between different IES codes.
- Most of these IES codes are the FORCE codes: https://ies.inl.gov/SitePages/FORCE.aspx
- Other codes are the Aspen HYSYS and the Aspen APEA:
https://www.aspentech.com/en/products/engineering/aspen-hysys
https://www.aspentech.com/en/products/pages/aspen-process-economic-analyzer
- ASPEN HYSYS And Aspen APEA ARE not part of the FORCE tools but they provide useful information such as:
- Steady state models for the IES configruation
- The costs of the IES components that are used to create cost functions.
-An example of the intgration of the Aspen HYSYS, APEA, FORCE tools is in the following report:
https://www.osti.gov/biblio/1890160

To faciliate this integration, vaious classes and methods are created. This code includes the following:


1 - A Python Class for the "FORCE Component". "FORCE Component" is a component that combines the component's inforation from two (or more) codes.

2 - A Python Class for the "FORCE Component Set". The "FORCE Component Set" is set of components grouped together.
For example: grouping all the pumps together. The component set is created to produce the cost function of a specific component category (e.g. a pump or a turbine). It is also needed to create a component set to be used in HERON.

3- Python Methods to extract all the  "FORCE" components. This is useful if the user is extracting the information of several components from several output files.
"""
#####
# Section 0
# Importing libraries and modules

import os
import json
from collections import OrderedDict
import numpy as np
from scipy.optimize import curve_fit
import matplotlib as mpl
import matplotlib.pyplot as plt

#####
# Section 1:
# Python Classes for the APEA Component, HYSYS Component, FORCE component, and FORCE ComponentSet

class ForceComponent:
  """
    The "FORCE" component:
    "FORCE Component" is a component that combines the component's information from two (or more) codes.
    This class should combine any components as long as they are in the form of dictionaries
  """

  def __init__(self, codes_files):
    """
    Constructor
    @ In, codes_files, list, The list of component text files.
    Each file contains information from a different code (e.g. HYSYS or APEA) and each text file contains a dictionary.
    @ Out, None
    """
    self.codes_files=codes_files

  def component_info(self):
    """
    Extracting the FORCE info for one component
    @ In, None
    @ Out, force_dict,  dict, The component information ager merging information from two codes
    """
    dict_list=[]
    for code_file in self.codes_files:
      dict1 = json.load(open(code_file))
      dict_list.append(dict1)
    force_dict = {}
    for dict in dict_list:
      force_dict.update(dict)
    search_key = 'Component Name'
    available_components_names =[]
    redundant_keys = []
    for key in force_dict:
      if search_key in key:
        redundant_keys.append(key)
        available_components_names.append(force_dict.get(key))
    if len(set(available_components_names))>1:
      print("Error: The components' names are not similar")
    else:
      force_component_name =   available_components_names[1]
    force_dict['Component Name'] = force_component_name

    for key in redundant_keys:
      del force_dict[key]
    force_dict=OrderedDict(force_dict)
    force_dict.move_to_end('Component Name', last=False)
    return(force_dict)


class ForceComponentSet:
  """
    FORCE component_set class which is characterized by:
    1 - A list of components
    2 - Cost functions curve of the component set
    3 - The mean error due to the cost function curve fitting
    4 - The cost function equation coefficent A: reference price
    5- The cost function equation coefficent D': reference driver
    6- The cost function equation coefficient X: The scaling factor
  """
  def __init__(self, component_sets_file):
    """
    Constructor
    @ In, component_sets_file, str,
    The file that is is edited by the used to idnetify the sets of components that need to be grouped together
    @ Out, None
    """
    self.component_sets_file = component_sets_file

  def component_set_info(self):
    """
    Creating the component set and its the cost function
    @ In, None
    @ Out, comp_set_info_dict,  dict, A dictionay of the component set information
    """
    components_folder = self.component_sets_file.split('ComponentSetsFiles', 1)[0]

    # # # First we wanna know which components are avaiilable
    files = [f for f in os.listdir(components_folder) if os.path.isfile(os.path.join(components_folder, f)) if f.endswith('txt')]

    available_components, available_component_types = [], []

    for f in files:
      component_name =json.load(open(os.path.join(components_folder, f))).get('Component Name')
      component_type=json.load(open(os.path.join(components_folder, f))).get('HYSYS Category')
      available_components.append(component_name)
      available_component_types.append(component_type)
    all_included_components, all_included_powers, all_included_power_units, all_included_installed_costs=[], [], [], []

    component_sets_file_dict = json.load(open(self.component_sets_file))
    set_name = component_sets_file_dict.get("Set Name")
    if "Included Categories" in component_sets_file_dict:
      included_types = (component_sets_file_dict.get("Included Categories"))
      for type in included_types:
        if type not in available_component_types:
          print(f"The components category '{type}' does not exist")
        else:
          for f in files:
            component_type=json.load(open(os.path.join(components_folder, f))).get('HYSYS Category')
            if component_type == type:
              included_comp = json.load(open(os.path.join(components_folder,  f))).get('Component Name')
              all_included_components.append(included_comp)
              included_power = json.load(open(os.path.join(components_folder,  f))).get('HYSYS Power')
              all_included_powers.append(included_power)
              included_power_unit = json.load(open(os.path.join(components_folder, f))).get('HYSYS Power Units')
              all_included_power_units.append(included_power_unit)
              included_installed_cost_USD = json.load(open(os.path.join(components_folder, f))).get('APEA Installed Cost [USD]')
              all_included_installed_costs.append(included_installed_cost_USD)

    if "Included Components" in component_sets_file_dict:
      included_names = (component_sets_file_dict.get("Included Components"))
      for comp_name in included_names:
        if comp_name not in available_components:
          print(f"The component named '{comp_name}' does not exist")
        else:
          all_included_components.append(comp_name)
          for f in files:
            component_name=json.load(open(os.path.join(components_folder, f))).get('Component Name')
            if component_name == comp_name:
              included_power = json.load(open(os.path.join(components_folder,  f))).get('HYSYS Power')
              all_included_powers.append(included_power)
              included_power_unit = json.load(open(os.path.join(components_folder, f))).get('HYSYS Power Units')
              all_included_power_units.append(included_power_unit)
              included_installed_cost_USD = json.load(open(os.path.join(components_folder, f))).get('APEA Installed Cost [USD]')
              all_included_installed_costs.append(included_installed_cost_USD)

    # # Excluding components with unknown information or non reasonable info
    excluded_components_indices = []
    for i in range(len(all_included_components)):
      if float(all_included_powers[i])<=0 or all_included_powers[i] =="unknown":
        print('\033[91m', "\n", f"The component(s) '{all_included_components[i]}' will be excluded because of unknown or non-positive power value",  '\033[0m')
        excluded_components_indices.append(i)
      if all_included_power_units[i] not in ['kW', 'MW']:
        print('\033[91m', "\n", f"The component(s) '{all_included_components[i]}' will be excluded because of unknown power unit", '\033[0m')
        excluded_components_indices.append(i)

      if all_included_installed_costs[i]<=0:
            print('\033[91m', "\n", f"The component '{all_included_components[i]}' will be excluded because of non-positive cost", '\033[0m')
            excluded_components_indices.append(i)


    updated_components_set, updated_powers, updated_power_units, updated_costs=[], [], [], []
    for i in range(len(all_included_components)):
      if i not in excluded_components_indices:
        updated_components_set.append(all_included_components[i])
        updated_powers.append(all_included_powers[i])
        updated_power_units.append(all_included_power_units[i])
        updated_costs.append(all_included_installed_costs[i])

    # To ensure that the power units are the same
    common_unit=(max(set(updated_power_units), key=updated_power_units.count))
    updated_powers_same_unit=[0]*len(updated_powers)
    for i in range(len(updated_power_units)):
      if updated_power_units[i] !=common_unit:
        if common_unit == "kW":
          updated_powers_same_unit[i] = 1000*updated_powers[i]
        if common_unit == "MW":
          updated_powers_same_unit[i] = 0.001*updated_powers[i]
      else:
        updated_powers_same_unit[i] = updated_powers[i]

    reference_driver = max(updated_powers_same_unit)

    # (D/D') in the cost function
    capacity_ratio = []
    for p in updated_powers_same_unit:
        capacity_ratio.append(p/reference_driver )


    # # Curve fitting
    updated_costs_output = updated_costs
    popt, pcov  = curve_fit(lambda t, a, b: a * (t ** b), capacity_ratio, updated_costs_output)
    ref_price = popt[0]
    scaling_factor = popt[1]
    calculated_costs = ref_price*(capacity_ratio**scaling_factor)
    error = (100*(abs(updated_costs-calculated_costs) )/updated_costs)
    avg_error = round(sum(error)/len(error), 2)

    # The created dictionary of the component set
    comp_set_info_dict = {
                          "Component Set Name": set_name,
                          "Component Set file": self.component_sets_file,
                          "Included components": updated_components_set,
                          "Reference Driver": reference_driver,
                          "Reference Driver Power Units": common_unit,
                          "Reference Price (USD)": ref_price,
                          "Scaling Factor": scaling_factor,
                          "Fitting Average Error (%)": avg_error }

    # Plotting
    plt.figure()
    ax = plt.axes()
    ax.scatter(updated_powers_same_unit, updated_costs, label='APEA Cost')
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
    ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.1f}'))
    ax.grid()
    power_fitted = np.linspace(np.min(updated_powers_same_unit), np.max(updated_powers_same_unit), 100)
    capacity_ratio_fitted = np.linspace(np.min(capacity_ratio), np.max(capacity_ratio), 100)
    fitted_costs = ref_price*(capacity_ratio_fitted**scaling_factor)

    ax.plot(power_fitted, fitted_costs, 'k', label='Fitted Cost')
    reference_driver_rounded= round (reference_driver, 1)
    ref_price_rounded= round (ref_price, 1)
    scaling_factor_rounded = round (scaling_factor, 4)

    ax.set_title(f'Cost function curve of "{set_name}" \n Ref Driver = {reference_driver_rounded} {common_unit} \n Ref price(USD) = {ref_price_rounded} \n Scaling factor = {scaling_factor_rounded} \n MAPE = {avg_error } %', pad=12)
    ax.set_ylabel('Cost [USD]')
    ax.set_xlabel(f'Power in {common_unit}')
    ax.legend(bbox_to_anchor=(1,1), loc="upper right", bbox_transform=plt.gcf().transFigure)
    plt.tight_layout()

    output_file = self.component_sets_file.split('txt', 1)[0] + 'png'
    file_exists = os.path.exists(output_file)
    if file_exists:
      os.remove(output_file)
    plt.savefig(output_file)

    print('\n', f'The components set "{set_name}" includes the following {len(updated_components_set)} components:','\n', updated_components_set)
    print('\n', f'The cost function of the component set "{set_name}" is produced and stored at: \n {output_file}')

    if len(updated_components_set) <3:
      print ('\n','\033[91m', f"Warning: The number of included components in the the component set '{set_name}' is only {len(updated_components_set)}. At least 3 components are required to produce the cost function curve", '\033[0m')

    return comp_set_info_dict


#####
# Section 2:
# Python Methods extracing all the FORCE components

def extract_all_force_components(folders_paths_list):
  """
    Extracting all the the FOCE components (by merging components from differetn codes)
    @ In, folders_paths_list, list, The list of component folder.
    Each foldes includes components created by a different code (e.g. HYSYS or APEA).
    @ Out, None
  """
  current_path= (os.path.abspath(__file__))
  force_outputs_path = current_path.split('/src', 1)[0]+"/FORCE_Components/"

  # Since somtimes we have components with the same name (e.g. turbine) but have different characteristics,
  # we added a suffix to the filename to be able to distinguish between components from different sources
  codes_suffix = ["APEA.xlsx", "HYSYS.xlsx", "HERON.xml", "HYBRID.txt"]
  for string in codes_suffix:
    if os.path.dirname(folders_paths_list[0]).endswith(string):
      suffix = (str(os.path.dirname(folders_paths_list[0]))).strip(string)
  filename_suffix = "_"+ suffix.split("/")[-1].replace(" ", "")

  files_list = [] # the list of lists of files in eac folder
  for folder_path in folders_paths_list:
    files_list.append(os.listdir(folder_path))
  common_components = set(files_list[0])
  for item in files_list[1:]:
    common_components.intersection_update(item)

  for comp in common_components:
    codes_files_list=[]
    for folder_path in folders_paths_list:
      filepath= folder_path+comp
      codes_files_list.append(filepath)
    component_1 = ForceComponent(codes_files_list)

    output_file = force_outputs_path+str(component_1.component_info().get('Component Name')).replace(" ", "").replace('/', '_')+filename_suffix +".txt"

    file_exists = os.path.exists(output_file)
    if file_exists:
      os.remove(output_file)
    json.dump(component_1.component_info(), open(output_file, 'w'),indent = 2)
  print(f" \n {len(common_components)} Force components are created at: {force_outputs_path } by combining info from: \n {folders_paths_list} \n")


def create_all_force_components_from_hysys_apea(folder1, folder2):
  """
    This method is similar to the previous "extract_all_force_components"
    The difference is that it works on several folders (of output files) at the same time and
    This method connects the HYSYS file with its corresponding APEA file

    @ In, folders_paths_list, list, The list of component folder. Each foldes includes components created by a different code (e.g. HYSYS or APEA).
    @ Out, None
  """
  # one folder is the Aspen HYSES folder and the other is the APEA one
  fol1_list = os.listdir(folder1)
  fol2_list = os.listdir(folder2)
  for i in range (len(fol1_list)):
    fol1_list[i] =  folder1 +"/" +fol1_list[i]
  for i in range (len(fol2_list)):
    fol2_list[i] =  folder2 + "/"+fol2_list[i]
  tot_list = fol1_list +  fol2_list

  aspen_apea_files_paths  = []
  for item in tot_list:
    if item.endswith ("HYSYS.xlsx"):
      hysys_model_name = item.strip('HYSYS.xlsx')
      aspen_apea_files_paths.append(hysys_model_name)
    if item.endswith ("APEA.xlsx"):
      apea_model_name = item.strip('APEA..xlsx')
      aspen_apea_files_paths.append(apea_model_name)

  aspen_apea_file_names = []
  for filepath in aspen_apea_files_paths:
    filename = os.path.basename(filepath)
    aspen_apea_file_names.append(filename)

  duplicate_file_names = set([x for x in aspen_apea_file_names if aspen_apea_file_names.count(x) > 1])

  hyses_filepaths =[]
  apea_filepaths =[]
  for filename in duplicate_file_names:
    for filepath in tot_list:
      if filepath.endswith(filename+ "HYSYS.xlsx"):
        hyses_filepaths.append(filepath+"/")
      if filepath.endswith(filename+ "APEA.xlsx"):
        apea_filepaths.append(filepath+"/")

  for i in range(len(hyses_filepaths)):
    extract_all_force_components([hyses_filepaths[i], apea_filepaths[i]])




def extract_all_force_componentsets(component_sets_folder):
  """
    Extracting ALL the component sets
    @ In, component_sets_folder, str, The path of the folder that includes several files of the user-input files
    These user-input files determine the components which will be grouped together in one set
    @ Out, None
  """
  for Setfile in os.listdir(component_sets_folder):
    if Setfile.startswith("Setfile") and Setfile.endswith(".txt"):
      print('\033[1m', f"\n\n A component set is found in '{Setfile}'", '\033[0m')
      Setfile_path = component_sets_folder + Setfile
      componentSet_dict = ForceComponentSet(Setfile_path).component_set_info()

      output_file_path = Setfile_path.replace("Setfile", "componentSet")
      file_exists = os.path.exists(output_file_path)
      if file_exists:
        os.remove(output_file_path)
      json.dump(componentSet_dict, open(output_file_path, 'w'), indent = 2)
      print(" \n", f"The new component set can be found at {output_file_path}")
