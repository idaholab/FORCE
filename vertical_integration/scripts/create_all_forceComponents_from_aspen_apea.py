# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
Creating ALL the "FORCE" components by looking into folders that contains output files from Aspen HYSYS and Aspen APEA

It takes the following arguments.
1-  The folder containing the HYSYS output XLSX files
2- The folder containing the APEA output XLSX files

Example:
python create_all_forceComponents_from_aspen_apea.py ../APEA/APEA_components ../HYSYS/HYSYS_components
"""
#!/usr/bin/env python
import argparse
import sys
import os
# import from the vertical_inegration/src
sys.path.append(os.path.dirname(__file__).split("vertical_integration")[:-1][0]+"vertical_integration/src")
from main_methods import create_all_force_components_from_hysys_apea

# User inputs
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="create FORCE components using components info from Aspen Hyses and APEA components"
  )
  # Inputs from the user
  parser.add_argument("folder1_HYSES_or_APEA", help="folder1_HYSES_or_APEA")
  parser.add_argument("folder2_HYSES_or_APEA", help="folder2_HYSES_or_APEA")
  args = parser.parse_args()

  create_all_force_components_from_hysys_apea(args.folder1_HYSES_or_APEA, args.folder2_HYSES_or_APEA)
