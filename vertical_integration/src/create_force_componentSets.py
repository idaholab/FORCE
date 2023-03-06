import argparse
from main import extract_all_force_componentSets


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="create FORCE componentSet and its cost function given the folder that contains the setfiles. Setfiles are files that list the components that the user wants to group together as one list"
  )
  # Inputs from the user
  parser.add_argument("componentSets_folder", help="The paths of folders that contain the setfiles. Setfiles are files that list the components that the user wants to group together as one list")
  args = parser.parse_args()

extract_all_force_componentSets(args.componentSets_folder)

### Example:
# python create_force_componentSets.py ../FORCE_Components/ComponentSetsFiles/Sets1/
####
