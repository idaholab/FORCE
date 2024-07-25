import os
import sys
import unittest
from unittest.mock import mock_open, patch, call, MagicMock
import xml.etree.ElementTree as ET

FORCE_LOC = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
sys.path.append(FORCE_LOC)
from FORCE.src.heron import create_componentsets_in_HERON

class HERONTestCase(unittest.TestCase):
  
  def check_reference_price(self, cashflow, correct_value, correct_content_length=1):
    ref_price = cashflow.findall('./reference_price')
    self.assertEqual(len(ref_price), 1)
    ref_price_contents = [e for e in ref_price[0].findall('./')
                          if not e.tag is ET.Comment] # Filters out ET.Comment elements
    self.assertEqual(len(ref_price_contents), correct_content_length)
    ref_price_value = ref_price[0].findall('./fixed_value')
    self.assertEqual(ref_price_value[0].text, correct_value)

  def check_reference_driver(self, cashflow, correct_value, correct_content_length=1):
    ref_driver = cashflow.findall('./reference_driver')
    self.assertEqual(len(ref_driver), 1)
    ref_driver_contents = [e for e in ref_driver[0].findall('./')
                          if not e.tag is ET.Comment] # Filters out ET.Comment elements
    self.assertEqual(len(ref_driver_contents), correct_content_length)
    ref_driver_value = ref_driver[0].findall('./fixed_value')
    self.assertEqual(ref_driver_value[0].text, correct_value)

  def check_scaling_factor(self, cashflow, correct_value, correct_content_length=1):
    scaling_factor = cashflow.findall('./scaling_factor_x')
    self.assertEqual(len(scaling_factor), 1)
    scaling_factor_contents = [e for e in scaling_factor[0].findall('./')
                               if not e.tag is ET.Comment] # Filters out ET.Comment elements
    self.assertEqual(len(scaling_factor_contents), correct_content_length)
    scaling_factor_value = scaling_factor[0].findall('./fixed_value')
    self.assertEqual(scaling_factor_value[0].text, correct_value)

class TestMinimalInput(HERONTestCase):

  def setUp(self):
    # Example of a minimal XML structure
    self.heron_xml = """<HERON>
                          <Components>
                            <Component name="ExistingComponent">
                              <economics>
                                <CashFlow name="ExistingComponent_capex">
                                </CashFlow>
                              </economics>
                            </Component>
                          </Components>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))

  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  @patch('builtins.open',
         new_callable=mock_open,
         read_data="""{
                          "Component Set Name": "NewComponent",
                          "Reference Driver": 1000,
                          "Reference Driver Power Units": "kW",
                          "Reference Price (USD)": 2000,
                          "Scaling Factor": 0.5
                      }""")
  def test_minimal_input(self, mock_file, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = ['componentSetFake.json']

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify the XML was updated correctly
    new_components = result_tree.findall('.//Component[@name="NewComponent"]')
    self.assertEqual(len(new_components), 1)
    economics = new_components[0].find('economics')
    self.assertIsNotNone(economics)

    # Verify the CashFlow node was created with attribs
    cashflows = economics.findall('CashFlow')
    self.assertEqual(len(cashflows), 1)
    self.assertEqual(cashflows[0].attrib['name'], 'NewComponent_capex')
    self.assertIn('type', cashflows[0].keys())
    self.assertIn('taxable', cashflows[0].keys())
    self.assertIn('inflation', cashflows[0].keys())
    
    # Verify reference price and reference driver
    self.check_reference_driver(cashflows[0], '1.0')
    self.check_reference_price(cashflows[0], '-2000')
 
class TestExpandedInput1(HERONTestCase):
  
  def setUp(self):
    # Added case and datagenerator nodes (should be transferred blindly) and extra components
    self.heron_xml = """<HERON>
                          <Case>
                            <untouched_content_Case></untouched_content_Case>
                          </Case>

                          <Components>
                            <Component name="ExistingComponent0">
                              <economics>
                                <CashFlow name="ExistingComponent0_capex" type="one-time">
                                  <untouched_content_EC0></untouched_content_EC0>
                                </CashFlow>
                              </economics>
                            </Component>

                            <Component name="ExistingComponent1">
                              <economics>
                                <CashFlow name="ExistingComponent1_fixed_OM" type="repeating">
                                  <untouched_content_EC1></untouched_content_EC1>
                                </CashFlow>
                              </economics>
                            </Component>
                          </Components>

                          <DataGenerators>
                            <untouched_content_DG></untouched_content_DG>
                          </DataGenerators>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))

  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  @patch('builtins.open',
         new_callable=mock_open,
         read_data="""{
                          "Component Set Name": "NewComponent",
                          "Reference Driver": 1000,
                          "Reference Driver Power Units": "mW",
                          "Reference Price (USD)": 2000,
                          "Scaling Factor": 0.5
                      }""")
  def test_expanded_input_1(self, mock_open, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    # No additional data for XML
    mock_listdir.return_value = ["componentSetFake.json"]

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify Case node was transferred
    with self.subTest("Case node has been corrupted"):
      cases = result_tree.findall('./Case')
      self.assertEqual(len(cases), 1)
      self.assertIsNotNone(cases[0].find('./untouched_content_Case'))

    # Verify Component nodes were merged
    component_nodes = result_tree.findall("./Components/Component")
    self.assertEqual(len(component_nodes), 3)

    for comp in component_nodes:
      cashflows = comp.findall('./economics/CashFlow')
      if comp.get('name') == 'ExistingComponent0':
        # Verify CashFlow with type
        self.assertEqual(len(cashflows), 1)
        self.assertEqual(cashflows[0].attrib['type'], 'one-time')
      elif comp.get('name') == 'ExistingComponent1':
        # Verify CashFlow with type
        self.assertEqual(len(cashflows), 1)
        self.assertEqual(cashflows[0].attrib['type'], 'repeating')
      elif comp.get('name') == 'NewComponent':
        # Verify reference driver
        self.check_reference_driver(cashflows[0], '1000')

    # Verify DataGenerators node was transferred
    with self.subTest("DataGenerators node has been corrupted"):
      data_gens = result_tree.findall('./DataGenerators')
      self.assertEqual(len(data_gens), 1)
      self.assertIsNotNone(data_gens[0].find('./untouched_content_DG'))

class TestExpandedInput2(HERONTestCase):
  
  def setUp(self):
    # Complex subnodes to each component with various <economics> and <CashFlows> positions and configurations
    self.heron_xml = """<HERON>
                          <Components>
                            <Component name="Component0">
                              <economics>
                                <CashFlow name="other">
                                  <untouched_content></untouched_content>
                                </CashFlow>
                              </economics>
                            </Component>

                            <Component name="Component1">
                              <produces resource="something">
                                <some_other_info></some_other_info>
                              </produces>
                              <economics>
                                <CashFlow name="other" type="one-time">
                                </CashFlow>
                                <CashFlow name="capex" type="one-time">
                                </CashFlow>
                              </economics>
                            </Component>

                            <Component name="Component2">
                              <economics>
                                <lifetime>1</lifetime>
                                <CashFlow name="capex_Comp2" npv_exempt="True">
                                  <reference_driver>
                                    <fixed_value>1234</fixed_value>
                                  </reference_driver>
                                  <reference_price>
                                    <ROM rom_stuff="stuff">more_rom_stuff</ROM>
                                  </reference_price>
                                  <scaling_factor_x>
                                    <uncertainty>
                                      <Uniform name="dist">
                                        <upperBound>8</upperBound>
                                        <lowerBound>0</lowerBound>
                                      </Uniform>
                                    </uncertainty>
                                  </scaling_factor_x>
                                  <driver>
                                    <fixed_value>1234</fixed_value>
                                  </driver>
                                </CashFlow>
                              </economics>
                            </Component>

                            <Component name="Component3">
                              <economics>
                                <CashFlow name="capex">
                                  <reference_driver></reference_driver>
                                  <scaling_factor_x></scaling_factor_x>
                                </CashFlow>
                              </economics>
                            </Component>
                          </Components>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))

  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  def test_expanded_input_2(self, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    # No additional data for XML
    mock_listdir.return_value = ["componentSetFake0.json", "componentSetFake1.json", "componentSetFake2.json", "componentSetFake3.json"]

    # Set up the open mock to return different files each time it's used
    mock_open_mult = mock_open()
    mock_open_mult.side_effect = [mock_open(read_data =
                                  """{
                                          "Component Set Name": "Component0",
                                          "Reference Driver": 1000,
                                          "Reference Driver Power Units": "mW",
                                          "Reference Price (USD)": 1000,
                                          "Scaling Factor": 0.1
                                      }""").return_value,
                                  mock_open(read_data =
                                  """{
                                          "Component Set Name": "Component1",
                                          "Reference Driver": 2100,
                                          "Reference Driver Power Units": "mW",
                                          "Reference Price (USD)": 2200,
                                          "Scaling Factor": 0.2
                                      }""").return_value,
                                  mock_open(read_data =
                                  """{
                                          "Component Set Name": "Component2",
                                          "Reference Driver": 3100,
                                          "Reference Driver Power Units": "mW",
                                          "Reference Price (USD)": 3200,
                                          "Scaling Factor": 0.3
                                      }""").return_value,
                                  mock_open(read_data =
                                  """{
                                          "Component Set Name": "Component3",
                                          "Reference Driver": 4100,
                                          "Reference Driver Power Units": "mW",
                                          "Reference Price (USD)": 4200,
                                          "Scaling Factor": 0.4
                                      }""").return_value]
                                    

    # Call the function with patch for open function
    with patch('builtins.open', mock_open_mult):
      result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify Component nodes were merged
    component_nodes = result_tree.findall("./Components/Component")
    self.assertEqual(len(component_nodes), 4)

    for comp in component_nodes:
      economics = comp.findall('./economics')
      self.assertEqual(len(economics), 1)

      if comp.get('name') == 'Component0':
        # Verify non-capex cashflow was not corrupted
        with self.subTest("Non-capex CashFlow node was corrupted"):
          cashflow_non_capex = economics[0].findall('./CashFlow[@name="other"]')
          self.assertEqual(len(cashflow_non_capex), 1)
          cf_noncap_contents = [e for e in cashflow_non_capex[0].findall('./')
                                if not e.tag is ET.Comment]  # Filters out ET.Comment elements
          self.assertEqual(len(cf_noncap_contents), 1)
          self.assertIsNotNone(cf_noncap_contents[0].tag, 'untouched_content')

        # Verify capex cashflow was added
        with self.subTest("capex CashFlow was not added correctly"):
          cashflow_capex = economics[0].findall('./CashFlow[@name="Component0_capex"]')
          self.assertEqual(len(cashflow_capex), 1)
        
      elif comp.get('name') == 'Component1':
        # Verify number of cashflows
        self.assertEqual(len(economics[0].findall('./CashFlow')), 2)

        # Verify non-capex cashflow was not corrupted
        with self.subTest("Non-capex CashFlow node was corrupted"):
          cashflow_non_capex = economics[0].findall('./CashFlow[@name="other"]')
          self.assertEqual(len(cashflow_non_capex), 1)
          self.assertEqual(cashflow_non_capex[0].attrib['type'], 'one-time')
          cashflow_noncap_contents = [e for e in cashflow_non_capex[0].findall('./')
                                      if not e.tag is ET.Comment] #  Filters out ET.Comment elements
          self.assertEqual(len(cashflow_noncap_contents), 0)

        # Verify capex cashflow was updated
        with self.subTest("capex CashFlow node was not updated correctly"):
          cashflow_capex = economics[0].findall('./CashFlow[@name="capex"]')
          self.assertEqual(len(cashflow_capex), 1)
          self.check_reference_price(cashflow_capex[0], '-2200')

      elif comp.get('name') == 'Component2':
        # Verify lifetime was not corrupted
        with self.subTest("Non-cashflow child node of economics has been corrupted"):
          proj_time = economics[0].findall('./lifetime')
          self.assertEqual(len(proj_time), 1)
          self.assertEqual(proj_time[0].text, '1')

        # Verify cashflow merging
        cashflows = economics[0].findall('./CashFlow')
        self.assertEqual(len(cashflows), 1)

        # Verify cashflow was updated correctly

        # Attributes
        with self.subTest("Attributes of CashFlow were corrupted"):
          self.assertIn('npv_exempt', cashflows[0].keys())
        
        # Children
        with self.subTest("CashFlow children nodes were not updated correctly"):
          cf_contents = [e for e in cashflows[0].findall('./')
                         if not e.tag is ET.Comment] # Filters out ET.Comment elements
          self.assertEqual(len(cf_contents), 4)

          self.check_reference_driver(cashflows[0], '3100')
          self.check_reference_price(cashflows[0], '-3200')
          self.check_scaling_factor(cashflows[0], '0.3')

        with self.subTest("Existing CashFlow child node was corrupted"):
          # Driver node
          driver = cashflows[0].findall('./driver')
          self.assertEqual(len(driver), 1)
          self.assertIsNotNone(driver[0].findall('fixed_value'))
      
      elif comp.get('name') == 'Component3':
        cashflows = comp.findall('./economics/CashFlow')
        self.assertEqual(len(cashflows), 1)

        # Verify cashflow was updated correctly
        with self.subTest("CashFlow children nodes were not updated correctly"):
          cf_contents = [e for e in cashflows[0].findall('./')
                         if not e.tag is ET.Comment] # Filters out ET.Comment elements
          self.assertEqual(len(cf_contents), 3)

          self.check_reference_driver(cashflows[0], '4100')
          self.check_reference_price(cashflows[0], '-4200')
          self.check_scaling_factor(cashflows[0], '0.4')

class TestNoComponentsNode(HERONTestCase):

  def setUp(self):
    # Has no Components node
    self.heron_xml = """<HERON>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))

  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  @patch('builtins.open',
         new_callable=mock_open,
         read_data="""{
                          "Component Set Name": "NewComponent",
                          "Reference Driver": 1000,
                          "Reference Driver Power Units": "mW",
                          "Reference Price (USD)": 2000,
                          "Scaling Factor": 0.5
                      }""")
  def test_no_comps_node(self, mock_file, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = ['componentSetFake.json']

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify components node was created with contents
    components = result_tree.findall('./Components')
    self.assertEqual(len(components), 1)
    self.assertEqual(len(components[0].findall('./Component[@name="NewComponent"]')), 1)

class TestNoComponentNodes(HERONTestCase):

  def setUp(self):
    # Has no Component nodes
    self.heron_xml = """<HERON>
                          <Components>
                          </Components>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))

  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  @patch('builtins.open',
         new_callable=mock_open,
         read_data="""{
                          "Component Set Name": "NewComponent",
                          "Reference Driver": 1000,
                          "Reference Driver Power Units": "kW",
                          "Reference Price (USD)": 2000,
                          "Scaling Factor": 0.5
                      }""")
  def test_no_comp_nodes(self, mock_file, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = ['componentSetFake.json']

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify component node was created
    component_list = result_tree.findall('./Components/Component')
    self.assertEqual(len(component_list), 1)
    self.assertEqual(component_list[0].attrib['name'], 'NewComponent')

    # Verify contents have been added
    self.assertIsNotNone(component_list[0].findall('./economics/CashFlow'))

class TestMissingSubnodes(HERONTestCase):

  def setUp(self):
    # Comp0 has no economics subnode; Comp1 has no CashFlow subnode
    self.heron_xml = """<HERON>
                          <Components>
                            <Component name="Component0">
                            </Component>

                            <Component name="Component1">
                              <economics>
                              </economics>
                            </Component>
                          </Components>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))

  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  def test_missing_subnodes(self, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = ['componentSetFake0.json', 'componentSetFake1.json']
    
    # Set up the open mock to return different files each time it's used
    mock_open_mult = mock_open()
    mock_open_mult.side_effect = [mock_open(read_data =
                                  """{
                                          "Component Set Name": "Component0",
                                          "Reference Driver": 1000,
                                          "Reference Driver Power Units": "mW",
                                          "Reference Price (USD)": 1000,
                                          "Scaling Factor": 0.1
                                      }""").return_value,
                                  mock_open(read_data =
                                  """{
                                          "Component Set Name": "Component1",
                                          "Reference Driver": 2000,
                                          "Reference Driver Power Units": "mW",
                                          "Reference Price (USD)": 2000,
                                          "Scaling Factor": 0.2
                                      }""").return_value]

    # Call the function with patch for open function
    with patch('builtins.open', mock_open_mult):
      result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify component nodes
    comp0 = result_tree.findall('./Components/Component[@name="Component0"]')
    self.assertEqual(len(comp0), 1)
    comp1 = result_tree.findall('./Components/Component[@name="Component1"]')
    self.assertEqual(len(comp1), 1)
    
    # Verify comp0 updated correctly
    with self.subTest("economics node and subnodes were not added correctly"):
      economics = comp0[0].findall('./economics')
      self.assertEqual(len(economics), 1)
      cashflows = economics[0].findall('./CashFlow')
      self.assertEqual(len(cashflows), 1)
      self.check_reference_driver(cashflows[0], '1000')

    # Verify comp1 updated correctly
    with self.subTest("cashflow node and subnodes were not added correctly"):
      cashflows = comp1[0].findall('./economics/CashFlow')
      self.assertEqual(len(cashflows), 1)
      self.check_reference_driver(cashflows[0], '2000')

class TestEmptyCompSetsFolder(HERONTestCase):
  def setUp(self):
    # Example of a minimal XML structure
    self.heron_xml = """<HERON>
                          <Components>
                            <Component name="ExistingComponent">
                              <economics>
                                <CashFlow name="ExistingComponent_capex">
                                </CashFlow>
                              </economics>
                            </Component>
                          </Components>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))
  
  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  # This mock_open should not be called in the function
  @patch('builtins.open',
         new_callable=mock_open,
         read_data="""{
                          "Component Set Name": "NewComponent",
                          "Reference Driver": 1000,
                          "Reference Driver Power Units": "kW",
                          "Reference Price (USD)": 2000,
                          "Scaling Factor": 0.5
                      }""")
  def test_empty_compsets_folder(self, mock_open, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = []

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify open function was not called
    mock_open.assert_not_called()

    components_nodes = result_tree.findall('./Components')

    # Verify component node was not corrupted
    component_nodes = components_nodes[0].findall('./Component')
    self.assertEqual(len(component_nodes), 1)
    self.assertEqual(component_nodes[0].attrib['name'], 'ExistingComponent')

class TestCompSetsFolderWithBadJSON(HERONTestCase):
  def setUp(self):
    # Example of a minimal XML structure
    self.heron_xml = """<HERON>
                          <Components>
                            <Component name="ExistingComponent">
                              <economics>
                                <CashFlow name="ExistingComponent_capex">
                                </CashFlow>
                              </economics>
                            </Component>
                          </Components>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))
  
  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  @patch('builtins.open',
         new_callable=mock_open,
         read_data="Example of bad format")
  def test_compsets_folder_bad_json(self, mock_open, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = ['componentSetFake.json']

    # Call the function and check for error
    caught_bad_json = False
    try:
      result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")
    except ValueError:
      caught_bad_json = True
    
    with self.subTest("Did not respond correctly to bad component set file content"):
      self.assertEqual(caught_bad_json, True)

class TestCompSetsFolderMultFiles(HERONTestCase):
  def setUp(self):
    # Example of a minimal XML structure
    self.heron_xml = """<HERON>
                          <Components>
                            <Component name="ExistingComponent">
                              <economics>
                                <CashFlow name="ExistingComponent_capex">
                                </CashFlow>
                              </economics>
                            </Component>
                          </Components>
                        </HERON>"""
    self.tree = ET.ElementTree(ET.fromstring(self.heron_xml))
  
  @patch('xml.etree.ElementTree.parse')
  @patch('os.listdir')
  # Open mock will return the same read_data each time it is called
  # This is acceptable only because the content of the result tree is untested
  @patch('builtins.open',
         new_callable=mock_open,
         read_data="""{
                          "Component Set Name": "NewComponent",
                          "Reference Driver": 1000,
                          "Reference Driver Power Units": "mW",
                          "Reference Price (USD)": 2000,
                          "Scaling Factor": 0.5
                      }""")
  def test_compsets_folder_mult_files(self, mock_open, mock_listdir, mock_parse):
    # Set up the parse mock to return an XML tree
    mock_parse.return_value = self.tree
    files_list = ['component.json', 'README', 'componentSet.csv', 'xcomponentSet.json',
                  'componentSet.json', 'componentSetStuff.txt',
                  'aFolder', 'Set.json', 'compSet.json', 'ComponentSet.json']
    mock_listdir.return_value = files_list
    # Only the txt and json files whose names start with 'componentSet' should be opened
    acceptable_files = ['componentSet.json', 'componentSetStuff.txt']

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify open function was called on correct files
    for file in files_list:
      # if file should have been opened
      if file in acceptable_files:
        with self.subTest(msg="File was not opened and should have been", file = file):
          # Verify file was opened
          self.assertIn(call('/fake/folder/'+file), mock_open.call_args_list)
      # if file should not have been opened
      else:
        with self.subTest(msg="File was opened and should not have been", file = file):
          # Verify file was not opened
          self.assertNotIn(call('/fake/folder/'+file), mock_open.call_args_list)

# This is not needed for running tests through FORCE/run_tests
# It does allow tests to be run via the unit tester when test_heron is run directly
if __name__ == '__main__':
  unittest.main()
