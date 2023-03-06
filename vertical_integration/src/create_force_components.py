import argparse
from main import extract_all_force_components

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="create FORCE components using components info from different codes"
  )
  #Inputs from the user
  parser.add_argument("codes_outputs_folders_paths", help="The paths of folders having components from different codes", nargs='+') # at least one terminal argument
  args = parser.parse_args()

extract_all_force_components(args.codes_outputs_folders_paths)

#Example
# python create_force_components.py ../APEA/APEA_components/from_Output_APEA.xlsx/ ../HYSYS/HYSYS_components/from_Output_HYSYS.xlsx/
