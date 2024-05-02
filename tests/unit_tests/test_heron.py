import unittest
from unittest.mock import mock_open, patch, MagicMock
import xml.etree.ElementTree as ET

from FORCE.src.heron import create_componentsets_in_HERON

class TestCreateComponentSetsInHERON(unittest.TestCase):

    def setUp(self):
        # Example of a minimal XML structure
        self.heron_xml = """<HERON>
                                <Components>
                                    <Component name="ExistingComponent">
                                        <economics>
                                            <CashFlow name="ExistingComponent_capex">
                                                <fixed_value>100</fixed_value>
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
    def test_new_component_creation(self, mock_file, mock_listdir, mock_parse):
        # Setup the mock to return an XML tree
        mock_parse.return_value = self.tree
        mock_listdir.return_value = ['componentSet1.json']

        # Call the function
        result_tree = create_componentsets_in_HERON("/fake/folder", "/fake/heron_input.xml")

        # Verify the XML was updated correctly
        components = result_tree.findall('.//Component[@name="NewComponent"]')
        self.assertEqual(len(components), 1)
        economics = components[0].find('economics')
        self.assertIsNotNone(economics)

        # Verify the CashFlow node was created
        cashflows = economics.findall('CashFlow')
        self.assertEqual(len(cashflows), 1)
        self.assertEqual(cashflows[0].attrib['name'], 'NewComponent_capex')

        # Verify the reference driver and price updates
        ref_driver = cashflows[0].find('./reference_driver/fixed_value')
        self.assertEqual(ref_driver.text, '1.0')  # The driver should have been converted from kW to MW

    # Add more tests here to cover other conditions and edge cases

if __name__ == '__main__':
    unittest.main()
