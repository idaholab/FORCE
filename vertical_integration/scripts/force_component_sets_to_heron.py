# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
A script that creates/updates the component sets in HERON from the componentSets text files.
This script to be used after the FORCE components are already created.

It takes the following arguments:
1 - A folder that contains the user-defined files that idntify which components to group together
2 - The initial HERON XML file that needs to be updated

Example:
python force_component_sets_to_heron.py ../FORCE_Components/ComponentSetsFiles/Sets1/ ../HERON/HERON_input_XML_files/heron_input.xml
"""
#!/usr/bin/env python
import os
import sys
import argparse

# import from the vertical_inegration/src
sys.path.append(os.path.dirname(__file__).split("vertical_integration")[:-1][0]+"vertical_integration/src")
from main_methods import create_componentsets_in_HERON
import convert_utils as xm

# Specifying user inputs and output file
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Create/update/add/modify the component Sets cashflow information from from the FORCE component Sets. These info are origianlly from Aspen Hyses and APEA"
    )
    # Inputs from the user
  parser.add_argument("Comp_Sets_Folder", help="The folder that includes all the FORCE component sets that have the info we want to import to HERON input XML file ")
  parser.add_argument("HERON_Input_XML", help="The original HERON input XML file to which the new component data are transferred")
  args = parser.parse_args()
  parnet_folder_name = os.path.abspath(os.path.join(args.HERON_Input_XML, os.pardir))
  filename = os.path.basename(args.HERON_Input_XML)

  new_HERON_tree = create_componentsets_in_HERON (args.Comp_Sets_Folder, args.HERON_Input_XML)

  output_file = parnet_folder_name+"/new_"+filename
  file_exists = os.path.exists(output_file)
  if file_exists:
    os.remove(output_file)

  with open(output_file, "w", encoding="utf8") as out:
    print((xm.prettify(new_HERON_tree )), file=out)

  print (f" \n The new HERON file is updated/created at: '{output_file}' ")
