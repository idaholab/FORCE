Large Chemical Plant HERON input files
Author: Logan Williams Logan.Williams@INL.gov
Modified versions of input files used in INL/RPT-24-78505

These HERON files are used to identify the optimal reactor technology 
mix for a large chemical plant.  In this case three reactor technologies 
are evaluated, HTGRs, A-LWRs, and SFRs.  The chemical plant requires 
electricity, and steam at three pressures, HP, IP and LP.  To compare 
technologies a single large CHP is modeled at the component level with 
turbine between each steam condition.  The HTGR and SFR are able to 
produce heat that can be converted into HP steam through a turbine.  
The heat from an A-LWR likewise be converted into IP steam through a 
turbine, or to HP steam through a compressor.  All three reactors have
an independent fixed capacity thermal energy storage system. 
The steam and electric demand of the plant are modeled as fixed demands.
The plant has the ability to buy and sell from the gird, but this is 
undesirable, so both are modeled with two components.  One with somewhat 
realistic buy and sell prices but limited capacity, and one with 
unrealistically high buy prices and low sell prices, with larger 
capacities. To allow the outer loop optimization to be flexible 
steam imports are also added, but because these are unrealistic the 
prices are extremely high.
