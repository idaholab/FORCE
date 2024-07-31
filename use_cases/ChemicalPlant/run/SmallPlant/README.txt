Small Chemical Plant HERON input files
Author: Logan Williams Logan.Williams@INL.gov
Modified versions of input files used in INL/RPT-24-78505

These HERON files are used to identify the optimal reactor and thermal energy 
storage size for a small chemical plant.  In this case the reactor is assumed 
to be a generic microreactor with a buffer two tank molten salt storage system.  
The chemical plant requires electricity, and steam. The steam and electric 
demands of the plant are modeled as fixed demands. The plant has the ability to 
buy a from the gird, not sell, but this is undesirable, so electric imports 
are modeled with two components.  One with somewhat realistic buy price but 
limited capacity, and one with unrealistically high buy price with a larger 
capacities. To allow the outer loop optimization to be flexible steam imports 
are also added, but because these are unrealistic the prices are extremely high.
