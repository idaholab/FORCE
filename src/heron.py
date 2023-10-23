# Copyright 2022, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED
"""
The objective of this code is the vertical integration (auomated data transfer) between different IES codes.
- Most of these IES codes are the FORCE codes: https://ies.inl.gov/SitePages/FORCE.aspx
- Other codes are the Aspen HYSYS and the Aspen APEA:
https://www.aspentech.com/en/products/engineering/aspen-hysys
https://www.aspentech.com/en/products/pages/aspen-process-economic-analyzer
- ASPEN HYSYS And Aspen APEA ARE not part of the FORCE tools but they provide useful information such as:
- Steady state models for the IES configruation
- The costs of the IES components that are used to create cost functions.
-An example of the intgration of the Aspen HYSYS, APEA, FORCE tools is in the following report:
https://www.osti.gov/biblio/1890160

To faciliate this integration, vaious classes and methods are created. This code includes the following:

 1 - A Python Method to create/update a component (or a component set) in HERON using the components' info from Aspen HYSYS and APEA
"""

#####
# Section 0
# Importing libraries and modules

import os
import json
from xml.etree import ElementTree as ET


# Section 1:
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
