"""
Creating the HYSYS components from the HYSYS output files.

It takes the following argument:
1 - A folder that contains the HYSYS xlxs output files

Example
python create_hysys_components.py ../HYSYS/HYSYS_outputs/
"""

import argparse
from main import extract_all_hysys_components

# # Specifying terminal command arguments
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Extract all the Aspen HYSES components"
  )
  # Inputs from the user
  parser.add_argument("hyses_xlsx_outputs_folder_path", help="hyses_xlsx_outputs_folder_path")
  args = parser.parse_args()

extract_all_hysys_components(args.hyses_xlsx_outputs_folder_path)
