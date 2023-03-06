import argparse
from main import extract_all_apea_components

# # Specifying terminal command arguments
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Extract all the APEA components"
  )
  # Inputs from the user
  parser.add_argument("apea_xlsx_outputs_folder_path", help="apea_xlsx_outputs_folder_path")
  args = parser.parse_args()

extract_all_apea_components(args.apea_xlsx_outputs_folder_path)

# Example
# python create_apea_components.py ../APEA/APEA_outputs/
