# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
A script that creates FORCE components from Aspen HYSYS and APEA xlsx outputs


It takes the following arguments:
1- The folder containing the HYSYS output XLSX files
2- The folder containing the APEA output XLSX files

Example:
python create_force_components.py HYSYS_outputs/ APEA_outputs/
"""

#!/usr/bin/env python
# Importing libraries and modules
import os
import sys
import argparse

# import from the vertical_inegration/src
sys.path.insert(1, os.path.dirname(__file__).rsplit("FORCE",maxsplit=2)[:-1][0]+"FORCE/src")
from hysys import extract_all_hysys_components
from apea import extract_all_apea_components
from force import create_all_force_components_from_hysys_apea


# Specifying user inputs and output file
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Starting by XLSX output files from aspen HYSYS and APEA, create the cost functions of components sets and create/upadate the component sets in the HERON input XML file"
    )
    # Inputs from the user
  parser.add_argument("hyses_xlsx_outputs_folder_path", help="hyses_xlsx_outputs_folder_path")
  parser.add_argument("apea_xlsx_outputs_folder_path", help="apea_xlsx_outputs_folder_path")
  args = parser.parse_args()
  
  print("\n",'\033[95m', "Step1 (creating HYSES and APEA components) begins", '\033[0m', "\n")
  hysys_comps_list = extract_all_hysys_components(args.hyses_xlsx_outputs_folder_path)[1]
  apea_comps_list = extract_all_apea_components(args.apea_xlsx_outputs_folder_path)[1]
  print("\n",'\033[95m', "Step1 (creating HYSES and APEA components) is complete", '\033[0m', "\n")

  print("\n",'\033[95m', "Step2 (creating HYSES and APEA FORCE components) begins", '\033[0m', "\n")
  FORCE_comps_list = create_all_force_components_from_hysys_apea( [hysys_comps_list, apea_comps_list ], args.hyses_xlsx_outputs_folder_path)[0]
  print("\n",'\033[95m', "Step2 (creating HYSES and APEA FORCE components) is complete", '\033[0m', "\n")
