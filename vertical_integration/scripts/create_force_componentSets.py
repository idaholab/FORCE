# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Running this script to create the "FORCE" component sets.
This script is used after the "FORCE" components are already created. Components sets are a set of components that are grouped together.

It takes the following arguments:
1- A folder that contains the user-defined files that idntify which components to group together
Example:
python create_force_componentSets.py ../FORCE_Components/ComponentSetsFiles/Sets1/
"""
#!/usr/bin/env python
import argparse
import sys
import os
# import from the vertical_inegration/src
sys.path.append(os.path.dirname(__file__).split("vertical_integration")[:-1][0]+"vertical_integration/src")
from main_methods import extract_all_force_componentsets

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="create FORCE componentSet and its cost function given the folder that contains the setfiles. Setfiles are files that list the components that the user wants to group together as one list"
  )
  # Inputs from the user
  parser.add_argument("componentSets_folder", help="The paths of folders that contain the setfiles. Setfiles are files that list the components that the user wants to group together as one list")
  args = parser.parse_args()

  extract_all_force_componentsets(args.componentSets_folder)
