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

    # Verify the CashFlow node was created
    cashflows = economics.findall('CashFlow')
    self.assertEqual(len(cashflows), 1)
    self.assertEqual(cashflows[0].attrib['name'], 'NewComponent_capex')

    # Verify the reference driver and price updates
    ref_driver = cashflows[0].find('./reference_driver/fixed_value')
    self.assertEqual(ref_driver.text, '1.0')  # The driver should have been converted from kW to MW
 
class TestExpandedInput(unittest.TestCase):
  
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
  def test_expanded_input(self, mock_open, mock_listdir, mock_parse):
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
    componentNodes = result_tree.findall("./Components/Component")
    self.assertEqual(len(componentNodes), 3)

    for comp in componentNodes:
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
        break

    # Verify DataGenerators node was transferred
    with (self.subTest("DataGenerators node has been corrupted")):
      dataGens = result_tree.findall('./DataGenerators')
      self.assertEqual(len(dataGens), 1)
      self.assertIsNotNone(dataGens[0].find('./untouched_content_DG'))

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

    # FIXME: Check result

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
    mock_open_twice = unittest.mock.mock_open()
    mock_open_twice.side_effect = [
                                    unittest.mock.mock_open(read_data = 
                                    """{
                                            "Component Set Name": "Component0",
                                            "Reference Driver": 1000,
                                            "Reference Driver Power Units": "mW",
                                            "Reference Price (USD)": 1000,
                                            "Scaling Factor": 0.1
                                        }""").return_value,
                                    unittest.mock.mock_open(read_data = 
                                    """{
                                            "Component Set Name": "Component1",
                                            "Reference Driver": 2000,
                                            "Reference Driver Power Units": "mW",
                                            "Reference Price (USD)": 2000,
                                            "Scaling Factor": 0.2
                                        }""").return_value
                                  ]

    # Call the function with patch for open function
    with unittest.mock.patch('builtins.open', mock_open_twice):
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

if __name__ == '__main__':
  unittest.main()
