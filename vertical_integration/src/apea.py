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

1 - Python Class and method for the component info in Aspen APEA
"""
#####
# Section 0
# Importing libraries and modules

import os
import json
import shutil
import pandas as pd

#####
# Section 1:
# Python Classes for the APEA Component

class ApeaComponent:
  """
    The APEA component: the APEA component is defined by the component name and the APEA output xlsx file from which the component info is imported (it is possible to have two compoennts with the same name) from different xlsx APEA outputs
  """
  def __init__(self, xlsx_filename, component_name):
    """
    Constructor
    @ In, xlsx_filename, str, APEA output xlsx file from which the component info is imported
    @ In, component_name, str, the component name
    @ Out, None
    """
    self.xlsx_filename = xlsx_filename
    self.component_name = component_name

  def component_cost_info(self):
    """
    extracting the cost info of one component
    @ In, None
    @ Out, apea_comp_info,  dict, The component economic infomration extracted from the APEA code for a specific component
    """

    file_data= pd.read_excel(self.xlsx_filename, sheet_name='Equipment', skiprows=3)
    equipment_cost = file_data.loc[file_data['Name'] == self.component_name,  'Equipment Cost [USD]'].values[0]
    installed_cost = file_data.loc[file_data['Name'] == self.component_name,  'Installed Cost [USD]'].values[0]
    equipment_weight  = file_data.loc[file_data['Name'] == self.component_name,  'Equipment Weight [LBS]'].values[0]
    total_installed_weight = file_data.loc[file_data['Name'] == self.component_name, 'Total Installed Weight [LBS]'].values[0]

    apea_comp_info= {
                      "APEA Component Name": self.component_name,
                      "APEA Source":self.xlsx_filename,
                      "APEA Equipment Cost [USD]": equipment_cost.item(),
                      "APEA Installed Cost [USD]":installed_cost.item() ,
                      "APEA Equipment Weight [LBS]": equipment_weight.item(),"APEA Total Installed Weight [LBS]": total_installed_weight.item()}

    return apea_comp_info


#####
# Section 2:
# Python Method extracing all the APEA components

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
