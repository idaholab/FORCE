## Under work
from main import *
import convert_utils as xm
import argparse

# Specifying user inputs and output file
if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description="Starting by XLSX output files from aspen HYSYS and APEA, create the cost functions of components sets and create/upadate the component sets in the HERON input XML file"
    )
    # Inputs from the user
  parser.add_argument("hyses_xlsx_outputs_folder_path", help="hyses_xlsx_outputs_folder_path")
  parser.add_argument("apea_xlsx_outputs_folder_path", help="apea_xlsx_outputs_folder_path")
  parser.add_argument("componentSets_folder", help="The paths of folders that contain the setfiles. Setfiles are files that list the components that the user wants to group together as one list")
  parser.add_argument("HERON_Input_XML", help="The original HERON input XML file to which the new component data are transferred")

  args = parser.parse_args()


print("\n",'\033[95m',"Step1 (creating HYSES and APEA components) begins", '\033[0m',"\n")
hys_comp_dir = os.path.dirname(os.path.abspath(extract_all_hysys_components(args.hyses_xlsx_outputs_folder_path)))
apea_comp_dir = os.path.dirname(os.path.abspath(extract_all_apea_components(args.apea_xlsx_outputs_folder_path)))
print("\n",'\033[95m', "Step1 (creating HYSES and APEA components) is complete", '\033[0m', "\n")

print("\n",'\033[95m',"Step2 (creating HYSES and APEA FORCE components) begins", '\033[0m', "\n")
create_all_force_components_from_hysys_apea(apea_comp_dir, hys_comp_dir )
print("\n",'\033[95m',"Step2 (creating HYSES and APEA FORCE components) is complete", '\033[0m', "\n")

print("\n",'\033[95m',"Step3 (creating FORCE componentsSets) begins", '\033[0m', "\n")
extract_all_force_componentSets(args.componentSets_folder)
print("\n",'\033[95m',"Step3 (creating FORCE componentsSets) is complete", '\033[0m', "\n")

print("\n",'\033[95m',"Step4 (Component Sets are loaded to the HERON input XMl file) begins", '\033[0m', "\n")
new_HERON_tree = create_componentSets_in_HERON (args.componentSets_folder, args.HERON_Input_XML)

parnet_folder_name = os.path.abspath(os.path.join(args.HERON_Input_XML, os.pardir))
filename = os.path.basename(args.HERON_Input_XML)


output_file = parnet_folder_name+"/new_"+filename
file_exists = os.path.exists(output_file)
if file_exists:
  os.remove(output_file)

with open(output_file, "w", encoding="utf8") as out:
  print((xm.prettify(new_HERON_tree )), file=out)

print (f" \n The new HERON file is updated/created at: '{output_file}' ")
print("\n",'\033[95m',"Step4 (Component Sets are loaded to the HERON input XMl file) is complete", '\033[0m', "\n")

# Example:
# python aspen_to_heron.py ../HYSYS/HYSYS_outputs/ ../APEA/APEA_outputs/ ../FORCE_Components/ComponentSetsFiles/Sets1/ ../HERON/HERON_input_XML_files/heron_input.xml
