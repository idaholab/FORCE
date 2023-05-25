# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
A script that creates/updates the component sets in HERON from a set of Aspen HYSYS and APEA output xlsx files. The script also creates the components cost functions

This script combines the functionality of the following scripts:
(create_apea_components.py, create_hysys_components.py, create_all_forceComponents_from_aspen_apea, create_force_componentSets, force_component_sets_to_heron.py)

It takes the following arguments:
1- The folder containing the HYSYS output XLSX files
2- The folder containing the APEA output XLSX files
3- A folder that contains the user-defined files that idntify which components to group together
4- The initial HERON XML file that needs to be updated

Example:
python aspen_to_heron.py ../HYSYS/HYSYS_outputs/ ../APEA/APEA_outputs/ ../FORCE_Components/ComponentSetsFiles/Sets1/ ../HERON/HERON_input_XML_files/heron_input.xml
"""

#!/usr/bin/env python
# Importing libraries and modules
import os
import sys
import argparse

# import from the vertical_inegration/src
sys.path.append(os.path.dirname(__file__).split("vertical_integration")[:-1][0]+"vertical_integration/src")
from main_methods import extract_all_force_componentsets
import convert_utils as xm
from main_methods import extract_all_hysys_components, extract_all_apea_components, create_all_force_components_from_hysys_apea, extract_all_force_componentsets, create_componentsets_in_HERON


# Specifying user inputs and output file
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Starting by XLSX output files from aspen HYSYS and APEA, create the cost functions of components sets and create/upadate the component sets in the HERON input XML file"
    )
    # Inputs from the user
  parser.add_argument("hyses_xlsx_outputs_folder_path", help="hyses_xlsx_outputs_folder_path")
  parser.add_argument("apea_xlsx_outputs_folder_path", help="apea_xlsx_outputs_folder_path")
  parser.add_argument("componentSets_folder", help="The paths of folders that contain the setfiles. Setfiles are files that list the components that the user wants to group together as one list")
  parser.add_argument("HERON_Input_XML", help="The original HERON input XML file to which the new component data are transferred")
  args = parser.parse_args()

  print("\n",'\033[95m', "Step1 (creating HYSES and APEA components) begins", '\033[0m', "\n")
  hys_comp_dir = os.path.dirname(os.path.abspath(extract_all_hysys_components(args.hyses_xlsx_outputs_folder_path)))
  apea_comp_dir = os.path.dirname(os.path.abspath(extract_all_apea_components(args.apea_xlsx_outputs_folder_path)))
  print("\n",'\033[95m', "Step1 (creating HYSES and APEA components) is complete", '\033[0m', "\n")

  print("\n",'\033[95m', "Step2 (creating HYSES and APEA FORCE components) begins", '\033[0m', "\n")
  create_all_force_components_from_hysys_apea(apea_comp_dir, hys_comp_dir )
  print("\n",'\033[95m', "Step2 (creating HYSES and APEA FORCE components) is complete", '\033[0m', "\n")

  print("\n",'\033[95m', "Step3 (creating FORCE componentsSets) begins", '\033[0m', "\n")
  extract_all_force_componentsets(args.componentSets_folder)
  print("\n",'\033[95m', "Step3 (creating FORCE componentsSets) is complete", '\033[0m', "\n")

  print("\n",'\033[95m', "Step4 (Component Sets are loaded to the HERON input XMl file) begins", '\033[0m', "\n")
  new_HERON_tree = create_componentsets_in_HERON (args.componentSets_folder, args.HERON_Input_XML)

  parnet_folder_name = os.path.abspath(os.path.join(args.HERON_Input_XML, os.pardir))
  filename = os.path.basename(args.HERON_Input_XML)


  output_file = parnet_folder_name+"/new_"+filename
  file_exists = os.path.exists(output_file)
  if file_exists:
    os.remove(output_file)

  with open(output_file, "w", encoding="utf8") as out:
    print((xm.prettify(new_HERON_tree )), file=out)

  print (f" \n The new HERON file is updated/created at: '{output_file}' ")
  print("\n",'\033[95m',"Step4 (Component Sets are loaded to the HERON input XMl file) is complete", '\033[0m', "\n")
