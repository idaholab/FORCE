import argparse
from main import create_all_force_components_from_hysys_apea

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


# Example : python create_all_forceComponents_from_aspen_apea.py ../APEA/APEA_components ../HYSYS/HYSYS_components
