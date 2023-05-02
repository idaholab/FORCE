# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
The objective of this code is the vertical integration (auomated data transfer) between different IES codes.
To faciliate this integration, vaious classes and methods are created. This code includes the following:

1 - Python Classes for the component info in Aspen HYSYS, and Aspen APEA

2 - A Python Class for the "FORCE Component". "FORCE Component" is a component that combines the component's inforation from two (or more) codes.

3 - A Python Class for the "FORCE Component Set". The "FORCE Component Set" is set of components grouped together.
For example: grouping all the pumps together. The component set is created to produce the cost function of a specific component category (e.g. a pump or a turbine). It is also needed to create a component set to be used in HERON.

 4 - Python Methods to extract ALL the components (or "FORCE components). This is useful if the user is extracting the information of several components from several output files.

 5 - A Python Method to create/update a component (or a component set) in HERON using the components' info from Aspen HYSYS and APEA
"""
#####
# Section 0
# Importing libraries and modules

import os
import json
from collections import OrderedDict
import shutil
from xml.etree import ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from main_classes import ApeaComponent, AspenHysysComponent, ForceComponent, ForceComponentSet


#####
# Section 1:
# Python Methods extracing all the HYSYS, APEA, FORCE components

def extract_all_hysys_components(HYSYS_xlsx_outputs_folder_path):
  """
    Extracting all the Aspen HYSYS components
    @ In, HYSYS_xlsx_outputs_folder_path, str, The path of the folder that includes all the outut files from HYSYS
    @ Out, HYSYS_outputs_path, str, The folder that contains the components created from the HYSYS code
  """
  files_list = os.listdir(HYSYS_xlsx_outputs_folder_path)
  current_path= (os.path.abspath(__file__))

  for xlsxfile in files_list:
    if xlsxfile.endswith(".xlsx"):
      if xlsxfile[0].isalpha() or xlsxfile[0].isdigit():
        HYSYS_file_path = HYSYS_xlsx_outputs_folder_path +"/" +xlsxfile

        HYSYS_outputs_path = current_path.split('/src', 1)[0]+"/HYSYS/HYSYS_components/"+ "from_"+str(os.path.basename(HYSYS_file_path))+"/"
        isExist = os.path.exists(HYSYS_outputs_path)
        if isExist:
          shutil.rmtree(HYSYS_outputs_path)
        # Create a new directory
        os.makedirs(HYSYS_outputs_path)
        print("\n A new directory is created with all the Apsen HYSYS components at:",HYSYS_outputs_path, "\n")

        sheets_names = ['Expanders', 'Coolers', 'Pumps', 'Heaters', 'Tees', 'Mixers', 'Heat Exchangers']
        for sheet in sheets_names:
          HYSYS_file_data= pd.read_excel(HYSYS_file_path,sheet_name=sheet)
          headers=list(HYSYS_file_data.columns.values)
          unwanted_headers =[]
          for header in headers:
            if (header.__contains__("Unit")) or (header.__contains__("named")):
              unwanted_headers.append(header)
          real_headers = [i for i in headers if i not in unwanted_headers]
          for header in real_headers:
            component_1 = AspenHysysComponent(HYSYS_file_path,header)
            output_file = HYSYS_outputs_path+str(component_1.component_name).replace(" ", "").replace('/', '_')+".txt"
            # remove old file if exists
            file_exists = os.path.exists(output_file)
            if file_exists:
              os.remove(output_file)
            json.dump(component_1.component_info(), open(output_file, 'w'),indent = 2)

  return HYSYS_outputs_path


def extract_all_apea_components(apea_xlsx_outputs_folder_path):
  """
    Extracting all the Aspen APEA components
    @ In, apea_xlsx_outputs, str, The path of the folder that includes all the outut files from APEA
    @ Out, APEA_outputs_path, str, The folder that contains the components created from the Aspen APEA code
  """
  files_list = os.listdir(apea_xlsx_outputs_folder_path)
  current_path= (os.path.abspath(__file__))
  for xlsxfile in files_list:
    if xlsxfile.endswith(".xlsx"):
      if xlsxfile[0].isalpha() or xlsxfile[0].isdigit():
      #print(xlsxfile)
        apea_file_path = apea_xlsx_outputs_folder_path + "/"+xlsxfile
        apea_file_data= pd.read_excel(apea_file_path, sheet_name='Equipment',skiprows=3)

        APEA_outputs_path = current_path.split('/src', 1)[0]+"/APEA/APEA_components/"+ "from_"+str(os.path.basename(apea_file_path))+"/"
        isExist = os.path.exists(APEA_outputs_path)
        if isExist:
          shutil.rmtree(APEA_outputs_path)
        # Create a new directory
        os.makedirs(APEA_outputs_path)
        print("\n A new directory is created with all the APEA components at:",APEA_outputs_path, "\n")

        for ind in apea_file_data.index:
          component_1= ApeaComponent(apea_file_path, apea_file_data['Name'][ind])
          output_file = APEA_outputs_path + str(component_1.component_name).replace(" ", "").replace('/', '_')+".txt"
          # # remove old file if exists
          file_exists = os.path.exists(output_file)
          if file_exists:
            os.remove(output_file)
          json.dump(component_1.component_cost_info(), open(output_file, 'w'),indent = 2)

  return APEA_outputs_path


def extract_all_force_components(folders_paths_list):
  """
    Extracting all the the FOCE components (by merging components from differetn codes)
    @ In, folders_paths_list, list, The list of component folder.
    Each foldes includes components created by a different code (e.g. HYSYS or APEA).
    @ Out, None
  """
  current_path= (os.path.abspath(__file__))
  force_outputs_path = current_path.split('/src', 1)[0]+"/FORCE_Components/"

  # Since somtimes we have components with the same name (e.g. turbine) but have different characteristics,
  # we added a suffix to the filename to be able to distinguish between components from different sources
  codes_suffix = ["APEA.xlsx", "HYSYS.xlsx", "HERON.xml", "HYBRID.txt"]
  for string in codes_suffix:
    if os.path.dirname(folders_paths_list[0]).endswith(string):
      suffix = (str(os.path.dirname(folders_paths_list[0]))).strip(string)
  filename_suffix = "_"+ suffix.split("/")[-1].replace(" ", "")

  files_list = [] # the list of lists of files in eac folder
  for folder_path in folders_paths_list:
    files_list.append(os.listdir(folder_path))
  common_components = set(files_list[0])
  for item in files_list[1:]:
    common_components.intersection_update(item)

  for comp in common_components:
    codes_files_list=[]
    for folder_path in folders_paths_list:
      filepath= folder_path+comp
      codes_files_list.append(filepath)
    component_1 = ForceComponent(codes_files_list)

    output_file = force_outputs_path+str(component_1.component_info().get('Component Name')).replace(" ", "").replace('/', '_')+filename_suffix +".txt"

    file_exists = os.path.exists(output_file)
    if file_exists:
      os.remove(output_file)
    json.dump(component_1.component_info(), open(output_file, 'w'),indent = 2)
  print(f" \n {len(common_components)} Force components are created at: {force_outputs_path } by combining info from: \n {folders_paths_list} \n")


def create_all_force_components_from_hysys_apea(folder1, folder2):
  """
    This method is similar to the previous "extract_all_force_components"
    The difference is that it works on several folders (of output files) at the same time and
    This method connects the HYSYS file with its corresponding APEA file

    @ In, folders_paths_list, list, The list of component folder. Each foldes includes components created by a different code (e.g. HYSYS or APEA).
    @ Out, None
  """
  # one folder is the Aspen HYSES folder and the other is the APEA one
  fol1_list = os.listdir(folder1)
  fol2_list = os.listdir(folder2)
  for i in range (len(fol1_list)):
    fol1_list[i] =  folder1 +"/" +fol1_list[i]
  for i in range (len(fol2_list)):
    fol2_list[i] =  folder2 + "/"+fol2_list[i]
  tot_list = fol1_list +  fol2_list

  aspen_apea_files_paths  = []
  for item in tot_list:
    if item.endswith ("HYSYS.xlsx"):
      hysys_model_name = item.strip('HYSYS.xlsx')
      aspen_apea_files_paths.append(hysys_model_name)
    if item.endswith ("APEA.xlsx"):
      apea_model_name = item.strip('APEA..xlsx')
      aspen_apea_files_paths.append(apea_model_name)

  aspen_apea_file_names = []
  for filepath in aspen_apea_files_paths:
    filename = os.path.basename(filepath)
    aspen_apea_file_names.append(filename)

  duplicate_file_names = set([x for x in aspen_apea_file_names if aspen_apea_file_names.count(x) > 1])

  hyses_filepaths =[]
  apea_filepaths =[]
  for filename in duplicate_file_names:
    for filepath in tot_list:
      if filepath.endswith(filename+ "HYSYS.xlsx"):
        hyses_filepaths.append(filepath+"/")
      if filepath.endswith(filename+ "APEA.xlsx"):
        apea_filepaths.append(filepath+"/")

  for i in range(len(hyses_filepaths)):
    extract_all_force_components([hyses_filepaths[i], apea_filepaths[i]])




def extract_all_force_componentsets(component_sets_folder):
  """
    Extracting ALL the component sets
    @ In, component_sets_folder, str, The path of the folder that includes several files of the user-input files
    These user-input files determine the components which will be grouped together in one set
    @ Out, None
  """
  for Setfile in os.listdir(component_sets_folder):
    if Setfile.startswith("Setfile") and Setfile.endswith(".txt"):
      print('\033[1m', f"\n\n A component set is found in '{Setfile}'", '\033[0m')
      Setfile_path = component_sets_folder + Setfile
      componentSet_dict = ForceComponentSet(Setfile_path).component_set_info()

      output_file_path = Setfile_path.replace("Setfile", "componentSet")
      file_exists = os.path.exists(output_file_path)
      if file_exists:
        os.remove(output_file_path)
      json.dump(componentSet_dict, open(output_file_path, 'w'), indent = 2)
      print(" \n", f"The new component set can be found at {output_file_path}")


# Section 2:
# A Method to create/update a component (or a component set) in HERON using the components' info from Aspen HYSYS and APEA

def create_componentsets_in_HERON(comp_sets_folder, heron_input_xml):
  """
    Create/update components (componnet-sets) in HERON input file
    @ In, comp_sets_folder, str, The path of the folder that includes several files of the user-input files
    These user-inpit files determine the components which will be grouped together in one set
    @ In, heron_input_xml, str, The path of the original HERON xml file at which components will be updated/created
    @ Out, HERON_inp_tree, xml.etree.ElementTree.ElementTree, the updated HERON inut file (XML tree)
  """

  HERON_inp_tree = ET.parse(heron_input_xml)
  components_list = HERON_inp_tree.findall("Components")  # The "components" node
  if not components_list:
    print("\n", f"The 'Components' node is not found in the HERON input xml file: {heron_input_xml}")
  else:
    for components in components_list:
      component = components.findall("Component")
      heron_comp_list = []  # The list of compoenents
      for comp in component:
        heron_comp_list.append(comp.attrib["name"]) # The list of components found in the HERON input XML file
      print(f" \n The following components are already in the HERON input XML file:'{heron_comp_list}'")

  comp_set_files_list = os.listdir(comp_sets_folder)

  # Goin through the FORCE componentSets to extract relevant info
  for textfile in comp_set_files_list:
    if textfile.startswith('componentSet'):
      textfile_path = comp_sets_folder+"/"+textfile
      comp_set_dict = json.load(open(textfile_path))
      comp_set_name = comp_set_dict.get('Component Set Name')

      ref_driver = comp_set_dict.get('Reference Driver')
      ref_driver_units = comp_set_dict.get('Reference Driver Power Units')
      if ref_driver_units == "kW":
        ref_driver = ref_driver/1000
      ref_price = comp_set_dict.get('Reference Price (USD)')
      scaling_factor = comp_set_dict.get('Scaling Factor')

      fit_error = comp_set_dict.get('Fitting Average Error (%)')
      print(f" \n The FORCE component set '{comp_set_name}' is found")

      # if the component is already in the HERON file, it gets updated
      if comp_set_name in heron_comp_list:
        print(f"The component set {comp_set_name} already exists in the HERON XML input file and will be updated")
        for component in components_list:
          for comp in component:
            if comp.attrib["name"] == comp_set_name:
              for node in comp:

                # if the "economics" node is found in the component node
                if node.tag == "economics":
                  ECO_NODE_FOUND = "True"
                  print(f"The 'economics' node is found in the component {comp.attrib['name']}")
                  node.append(ET.Comment(f" Some of this component economic info are imported from: {textfile_path}"))
                  for subnode in node:
                    # If the cashflow node is found
                    if subnode.tag == "CashFlow":
                      if 'capex' in str(subnode.attrib["name"]):
                        print("The 'cashflow' subnode is found too and is updated")
                        Cashflow_NODE_FOUND = "True"
                        for subsubnode in subnode:
                          if subsubnode.tag in ['reference_driver', 'reference_price', 'scaling_factor_x']:
                            subnode.remove(subsubnode)
                        new_cash_node = subnode
                        new_cash_node.append(ET.Comment(f" Some of this component cashFlow info are imported from: {textfile_path}"))

                  try:
                    Cashflow_NODE_FOUND
                  # If cashflow node is not found
                  except NameError:
                    print(f"The 'CashFlow' subnode is not found under the 'economics' node in the component '{comp.attrib['name']}' and a new 'CashFlow' node is created")
                    new_cash_node = ET.SubElement(node, "CashFlow",
                                                  {'name': comp.attrib["name"]+"_capex",
                                                   'type': "one-time",
                                                   'taxable': "True",
                                                   'inflation':"None",
                                                   'mult_target': "False"} )
                    new_cash_node.append(ET.Comment(f" This component cashFlow info are imported from: {textfile_path}"))

              # if the economic node is not found in the component node
              try:
                ECO_NODE_FOUND
              except NameError:
                print(f"The 'economics' node is not found in the component '{comp.attrib['name']}' and a new 'economics' node is created")
                new_econ_node = ET.SubElement(comp, "economics")
                new_econ_node.append(ET.Comment(f" This component economic info are imported from: {textfile_path}"))

                new_cash_node = ET.SubElement(new_econ_node,
                                              "CashFlow",{
                                                'name': comp.attrib["name"]+"_capex",
                                                'type': "one-time",
                                                'taxable': "True",
                                                'inflation':"None",
                                                'mult_target': "False"} )
                new_cash_node.append(ET.Comment(f" Default values are assigned to the cashflow parameters and need to be reviewed by the user"))

      else:
        # if the component is not already in the HERON file, it is created.
        print(f"The component set '{comp_set_name}' is not found in the HERON XMl input file. The componnent node '{comp_set_name}' will be created")
        comp_name_dict = {'name': comp_set_name}
        for components in components_list:
          new_comp_node = ET.SubElement(components, "Component", comp_name_dict)
          new_comp_node.append(ET.Comment(f" This component info are imported from: {textfile_path}"))

          new_econ_node = ET.SubElement(new_comp_node, "economics")
          new_cash_node = ET.SubElement(new_econ_node, "CashFlow",{
            'name': comp_set_name+"_capex",
            'type': "one-time",
            'taxable': "True",
            'inflation':"None",
            'mult_target': "False"} )
          new_cash_node.append(ET.Comment(f" Default values are assigned to the cashflow parameters and need to be reviewed by the user"))

      ref_driver_node = ET.SubElement(new_cash_node, "reference_driver")
      ref_driver_val_node = ET.SubElement(ref_driver_node, "fixed_value")
      ref_driver_val_node.text = str(ref_driver)
      ref_driver_node.append(ET.Comment("Units : MW"))

      ref_price_node = ET.SubElement(new_cash_node, "reference_price")
      ref_price_val_node = ET.SubElement(ref_price_node, "fixed_value")
      ref_price_val_node.text = str(ref_price*(-1))
      ref_price_node.append(ET.Comment("Reference Price (USD)"))


      scaling_factor_node = ET.SubElement(new_cash_node, "scaling_factor_x")
      scaling_factor_val_node = ET.SubElement(scaling_factor_node, "fixed_value")
      scaling_factor_val_node.text = str(scaling_factor)
      new_cash_node.append(ET.Comment(f"Note that the cost function curve fitting error is {fit_error} %"))

  return HERON_inp_tree
