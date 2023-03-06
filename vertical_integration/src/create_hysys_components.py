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

# Example
# python create_hysys_components.py ../HYSYS/HYSYS_outputs/
