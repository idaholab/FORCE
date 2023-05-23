# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
This script creates the "FORCE" components.
"FORCE" components are components that merges info from two (or more) codes (e.g. Aspen HYSYS ans Aspen APEA)

It can take ANY number of arguments as it merges information of components from several codes.

1- A folder that continas the components text files.
Each text file is loaded with a component info (a dictionary).
All the files are created from one code (e.g. Aspeh HYSYS)

2- A folder that continas the components text files.
Each text file is loaded with a component info (a dictionary).
All the files are created from ANOTHER code (e.g. Aspeh APEA)

Example
python create_force_components.py ../APEA/APEA_components/from_Output_APEA.xlsx/ ../HYSYS/HYSYS_components/from_Output_HYSYS.xlsx/
"""
#!/usr/bin/env python
import argparse
import sys
import os
# import from the vertical_inegration/src
sys.path.append(os.path.dirname(__file__).split("vertical_integration")[:-1][0]+"vertical_integration/src")
from main_methods import extract_all_force_components


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="create FORCE components using components info from different codes"
  )
  #Inputs from the user
  parser.add_argument("codes_outputs_folders_paths", help="The paths of folders having components from different codes", nargs='+') # at least one terminal argument
  args = parser.parse_args()

  extract_all_force_components(args.codes_outputs_folders_paths)


