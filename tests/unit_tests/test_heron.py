import os
import sys
import unittest
from unittest.mock import mock_open, patch, MagicMock
import xml.etree.ElementTree as ET

FORCE_LOC = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir))
sys.path.append(FORCE_LOC)
from FORCE.src.heron import create_componentsets_in_HERON

class TestMinimalInput(unittest.TestCase):

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
    # Set up the mock to return an XML tree
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
    self.assertIn('mult_target', cashflows[0].keys())
    
    # Verify reference price
    ref_price_value = cashflows[0].find('./reference_price/fixed_value')
    self.assertEqual(ref_price_value.text, '-2000')

    # Verify the reference driver and price updates
    ref_driver_value = cashflows[0].find('./reference_driver/fixed_value')
    self.assertEqual(ref_driver_value.text, '1.0')  # The driver should have been converted from kW to MW
 
class TestExpandedInput1(unittest.TestCase):
  
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
    # Set up the mock to return an XML tree
    mock_parse.return_value = self.tree
    # No additional data for XML
    mock_listdir.return_value = ["componentSetFake.json"]

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify Case node was transferred
    with (self.subTest("Case node has been corrupted")):
      cases = result_tree.findall('./Case')
      self.assertEqual(len(cases), 1)
      self.assertIsNotNone(cases[0].find('./untouched_content_Case'))

    # Verify Component nodes were merged
    component_nodes = result_tree.findall("./Components/Component")
    self.assertEqual(len(component_nodes), 3)

    for comp in component_nodes:
      if comp.get('name') == 'ExistingComponent0':
        # Verify CashFlow with type
        cashflows = comp.findall('./economics/CashFlow')
        self.assertEqual(len(cashflows), 1)
        self.assertEqual(cashflows[0].attrib['type'], 'one-time')
      elif comp.get('name') == 'ExistingComponent1':
        # Verify CashFlow with type
        cashflows = comp.findall('./economics/CashFlow')
        self.assertEqual(len(cashflows), 1)
        self.assertEqual(cashflows[0].attrib['type'], 'repeating')
      elif comp.get('name') == 'NewComponent':
        # Verify reference driver
        ref_driver = comp.find('./economics/CashFlow/reference_driver/fixed_value')
        self.assertEqual(ref_driver.text, '1000') # Check that mW were not converted

    # Verify DataGenerators node was transferred
    with (self.subTest("DataGenerators node has been corrupted")):
      data_gens = result_tree.findall('./DataGenerators')
      self.assertEqual(len(data_gens), 1)
      self.assertIsNotNone(data_gens[0].find('./untouched_content_DG'))

class TestExpandedInput2(unittest.TestCase):
  
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
                                <ProjectTime>1</ProjectTime>
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
    # Set up the mock to return an XML tree
    mock_parse.return_value = self.tree
    # No additional data for XML
    mock_listdir.return_value = ["componentSetFake0.json", "componentSetFake1.json", "componentSetFake2.json", "componentSetFake3.json"]

    # Set up the open mock to return different files each time it's used
    mock_open_mult = mock_open()
    mock_open_mult.side_effect = [
                                    mock_open(read_data =
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
                                        }""").return_value
                                  ]

    # Call the function with patch for open function
    with patch('builtins.open', mock_open_mult):
      result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify Component nodes were merged
    component_nodes = result_tree.findall("./Components/Component")
    self.assertEqual(len(component_nodes), 4)

    for comp in component_nodes:
      if comp.get('name') == 'Component0':
        economics = comp.find('./economics')
        
        # Verify non-capex cashflow was not corrupted
        with self.subTest("Non-capex CashFlow node was corrupted"):
          cashflow_non_capex = economics.findall('./CashFlow[@name="other"]')
          self.assertEqual(len(cashflow_non_capex), 1)
          cf_noncap_contents = [e for e in cashflow_non_capex[0].findall('./')
                                if not e.tag is ET.Comment]  # Filters out ET.Comment elements
          self.assertEqual(len(cf_noncap_contents), 1)
          self.assertIsNotNone(cf_noncap_contents[0].tag, 'untouched_content')

        # Verify capex cashflow was added
        with self.subTest("capex CashFlow was not added correctly"):
          cashflow_capex = economics.findall('./CashFlow[@name="Component0_capex"]')
          self.assertEqual(len(cashflow_capex), 1)
        
      elif comp.get('name') == 'Component1':
        economics = comp.findall('./economics')
        self.assertEqual(len(economics), 1)

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
          ref_price = cashflow_capex[0].findall('./reference_price/fixed_value')
          self.assertEqual(ref_price[0].text, '-2200')

      elif comp.get('name') == 'Component2':
        economics = comp.findall('./economics')

        # Verify ProjectTime was not corrupted
        with self.subTest("Non-cashflow child node of economics has been corrupted"):
          proj_time = economics[0].findall('./ProjectTime')
          self.assertEqual(len(proj_time), 1)
          self.assertEqual(proj_time[0].text, '1')

        # Verify cashflow merging
        cashflow = economics[0].findall('./CashFlow')
        self.assertEqual(len(cashflow), 1)

        # Verify cashflow was updated correctly

        # Attributes
        with self.subTest("Attributes of CashFlow were corrupted"):
          self.assertIn('npv_exempt', cashflow[0].keys())
        
        # Children
        with self.subTest("CashFlow children nodes were not updated correctly"):
          cf_contents = [e for e in cashflow[0].findall('./')
                         if not e.tag is ET.Comment] # Filters out ET.Comment elements
          self.assertEqual(len(cf_contents), 4)

          # Reference driver
          ref_driver = cashflow[0].findall('./reference_driver')
          self.assertEqual(len(ref_driver), 1)
          ref_driver_value = ref_driver[0].findall('./fixed_value')
          self.assertEqual(ref_driver_value.text, '3100')

          # Reference price
          ref_price = cashflow[0].findall('./reference_price')
          self.assertEqual(len(ref_price), 1)
          ref_price_contents = [e for e in ref_price[0].findall('./')
                                if not e.tag is ET.Comment] # Filters out ET.Comment elements
          self.assertEqual(len(ref_price_contents), 1)
          ref_price_value = ref_price[0].findall('./fixed_value')
          self.assertEqual(ref_price_value[0].text, '-3200')

          # Scaling factor
          scaling_factor = cashflow[0].findall('./scaling_factor_x')
          self.assertEqual(len(scaling_factor), 1)
          scaling_factor_contents = [e for e in scaling_factor[0].findall('./')
                                     if not e.tag is ET.Comment] # Filters out ET.Comment elements
          self.assertEqual(len(scaling_factor_contents), 1)
          scaling_factor_value = scaling_factor[0].findall('./fixed_value')
          self.assertEqual(scaling_factor_value[0].text, '0.3')

        with self.subTest("Existing CashFlow child node was corrupted"):
          # Driver node
          driver = cashflow[0].findall('./driver')
          self.assertEqual(len(driver), 1)
          self.assertIsNotNone(driver[0].findall('fixed_value'))
      
      elif comp.get('name') == 'Component3':
        cashflow = comp.findall('./economics/CashFlow')
        self.assertEqual(len(cashflow), 1)

        # Verify cashflow was updated correctly
        with self.subTest("CashFlow children nodes were not updated correctly"):
          cf_contents = [e for e in cashflow[0].findall('./')
                         if not e.tag is ET.Comment] # Filters out ET.Comment elements
          self.assertEqual(len(cf_contents), 3)

          # Reference driver
          ref_driver = cashflow[0].findall('./reference_driver')
          self.assertEqual(len(ref_driver), 1)
          ref_driver_value = ref_driver[0].findall('./fixed_value')
          self.assertEqual(ref_driver_value.text, '4100')

          # Reference price
          ref_price = cashflow[0].findall('./reference_price')
          self.assertEqual(len(ref_price), 1)
          ref_price_value = ref_price[0].findall('./fixed_value')
          self.assertEqual(ref_price_value[0].text, '4200')

          # Scaling factor
          scaling_factor = cashflow[0].findall('./scaling_factor_x')
          self.assertEqual(len(scaling_factor), 1)
          scaling_factor_value = scaling_factor[0].findall('./fixed_value')
          self.assertEqual(scaling_factor_value[0].text, '0.4')

@unittest.skip("Waiting for function update")
class TestNoComponentsNode(unittest.TestCase):

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
    # Set up the mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = ['componentSetFake.json']

    # Call the function
    result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

    # Verify components node was created with contents
    components = result_tree.findall('./Components')
    self.assertEqual(len(components), 1)
    self.assertEqual(len(components[0].findall('./Component[@name="NewComponent"]')), 1)

class TestNoComponentNodes(unittest.TestCase):

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
    # Set up the mock to return an XML tree
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

class TestMissingSubnodes(unittest.TestCase):

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
    # Set up the mock to return an XML tree
    mock_parse.return_value = self.tree
    mock_listdir.return_value = ['componentSetFake0.json', 'componentSetFake1.json']
    
    # Set up the open mock to return different files each time it's used
    mock_open_twice = mock_open()
    mock_open_twice.side_effect = [
                                    mock_open(read_data =
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
                                        }""").return_value
                                  ]

    # Call the function with patch for open function
    with patch('builtins.open', mock_open_twice):
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
      self.assertEqual(cashflows[0].attrib["name"], "Component0_capex")
      ref_driver = cashflows[0].find('./reference_driver/fixed_value')
      self.assertEqual(ref_driver.text, "1000")

    # Verify comp1 updated correctly
    with self.subTest("cashflow node and subnodes were not added correctly"):
      cashflows = comp1[0].findall('./economics/CashFlow')
      self.assertEqual(len(cashflows), 1)
      self.assertEqual(cashflows[0].attrib["name"], "Component1_capex")
      ref_driver = cashflows[0].find('./reference_driver/fixed_value')
      self.assertEqual(ref_driver.text, "2000")

# This is not needed for running tests through FORCE/run_tests
# It does allow tests to be run via the unit tester when test_heron is run directly
if __name__ == '__main__':
  unittest.main()
