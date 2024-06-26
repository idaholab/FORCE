# Unit Testing
## HERON
The `test_heron.py` file contains unit tests for the `FORCE/src/heron/create_componentsets_in_HERON()` function. These are designed to help developers identify bugs and isolate their causes. To this end, a brief overview of the most important unique scenarios each unit test addresses is listed below.

### TestMinimalInput
This test is designed to check main functionality with minimal edge cases. It checks that:
- New Component node was added and updated with content, including:
  - economics node
  - capex CashFlow, with all attributes
  - reference price
  - reference driver, with conversion from kW to mW

### TestExpandedInput1
This test considers a more complex HERON input XML. It checks that:
- Case node is transferred uncorrupted
- Contents of multiple existing components that should not be updated are uncorrupted
- New component's reference driver value is not converted if input is in mW
- DataGenerators node is transferred uncorrupted

### TestExpandedInput2
This test focuses on ensuring correct updating of economics and CashFlow nodes and subnodes. It checks that:
- Multiple components that need updating can be merged correctly with new components
- Existing CashFlow of type non-capex is uncorrupted
- capex CashFlow is added when a non-capex CashFlow exists but a capex CashFlow does not
- economics node is found successfully when non-economics subnode of the component precedes the economics subnode
- CashFlows are updated correctly when both a non-capex and a capex CashFlow exists
- Non-CashFlow subnode of economics node is uncorrupted and CashFlow is still found
- Existing capex CashFlow has
  - Uncorrupted attributes
  - Uncorrupted subnode that does not need updating
  - All three existing subnodes that need updating correctly replaced
- CashFlow subnodes are updated correctly when two of the three types that need updating exist

### TestNoComponentsNode
This test examines a single edge case where the Components node is missing from the HERON input XML script. It checks that:
- A new Components node is created if one does not exist
- The new Component node is placed within this new Components node

### TestNoComponentNodes
This test examines the edge case where a Components node exists, but no Component nodes. It checks that:
- The new component is added, with content

### TestMissingSubnodes
This test considers scenarios where a component that needs to be updated is missing an economics or CashFlow subnode. It checks that:
- If the economics node is missing, it is created with correct content
- If the CashFlow node is missing, it is created with correct content

### TestEmptyCompSetsFolder
This test checks the function's behavior when the provided component set folder is empty. It checks that:
- The open function was not called (e.g., no file was opened)
- The existing component was not corrupted

### TestCompSetsFolderWithBadJSON
This test ensures a correct response to a component set file that is not is proper JSON format. It checks that:
- The function throws a ValueError

### TestCompSetsFolderMultFiles
This test checks the function's filtering system regarding which component set files it should open. It checks that:
- Only files whose names start with "componentSet" are opened
- Only files of type .txt or .json are opened