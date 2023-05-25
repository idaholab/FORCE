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

To faciliate this integration, this code includes the following
1 - Python Class and method for the component info in Aspen HYSYS
"""

#####
# Section 0
# Importing libraries and modules

import os
import json
import pandas as pd
import shutil

#####
# Section 1:
# Python Class for the HYSYS Component

class AspenHysysComponent:
  """
    The aspen HYSYS component:
    Aspen HYSYS component is defined by:
    1- The component name,
    2- The HYSYS output xlsx file from which the component info is imported
    It is possible to have two compoennts with the same name from different xlsx output files
  """
  def __init__(self, xlsx_filename, component_name):
    """
    Constructor
    @ In, xlsx_filename, str, HYSYS output xlsx file from which the component info is imported
    @ In, component_name, str, the component name
    @ Out, None
    """
    self.xlsx_filename = xlsx_filename
    self.component_name = component_name

  def component_info(self):
    """
    extracting the relevant info one component
    @ In, None
    @ Out, HYSYS_comp_info,  dict, The component relevant infomration extracted from the HYSYS code for a specific component
    """

    sheets_names = ['Expanders', 'Coolers', 'Pumps', 'Heaters', 'Tees', 'Mixers', 'Heat Exchangers']
    for sheet in sheets_names:
      headers =list(pd.read_excel(self.xlsx_filename, sheet_name= sheet).columns.values)
      if self.component_name in headers:
        df = pd.read_excel(self.xlsx_filename, sheet_name= sheet)
        keywords = ['POWER' , 'Power' , 'DUTY' , 'Duty']
        capacity = (list(set(keywords).intersection(df.iloc[:, 0].values)))
        if len(capacity):
          power = df.loc[df.iloc[:, 0] == capacity[0] , self.component_name].values[0]
          power_unit = df.loc[df.iloc[:, 0] == capacity[0] , "Unit"].values[0]
        else:
          power ="unknown"
          power_unit = "unknown"

        HYSYS_comp_info= {
                          "HYSYS Component Name": self.component_name,
                          "HYSYS Category": sheet,
                          "HYSYS Source":self.xlsx_filename,
                          "HYSYS Power": power,
                          "HYSYS Power Units":power_unit}
    return HYSYS_comp_info


#####
# Section 2:
# Python Method extracing all the HYSYS components

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
