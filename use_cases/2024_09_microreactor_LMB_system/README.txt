Cases for LDRD Milestone due 2024-09-30.

PI: Tyler L. Westover
Sponsor: The Idaho National Laboratory (INL) Laboratory Directed Research and Development (LDRD) Program under Department of Energy (DOE) Idaho Operations Office Contract DE-AC07-05ID14517
Code Executor: So-Bin Cho
Data Support Contact: So-Bin Cho (sobin.cho@inl.gov)
Contributors: Sam J. Root, Rami M. Saeed, and Tyler L. Westover

Description:
ARMA synthetic models are used to generate synthetic price signals for ERCOT, PJM, and MISO. HERON input takes synthetic profile files and specifications of HTGR-Liquid Metal Battery (LMB) system to assess optimal sizing and economics (Net Present Value, NPV) in the individual markets.

Data for the historical Realtime Locational Marginal Price (LMP) from ERCOT, PJM, and MISO are used to train synthetic data models. The optimal sizes of nuclear-TES systems are examined based on 120-hour (73 clusters).

For details on generating these files, please refer to the RAVEN wiki (https://github.com/idaholab/raven/wiki/runningRAVEN). 

HERON input files are in ./HERON. Iput XML files generate RAVEN inner.xml and outer.xml files, optimizing componentsÕ dispatch and size, respectively. To run these input files, HERON must be installed as part of the RAVEN plugin (https://github.com/idaholab/HERON/wiki).   

./results folder contains all results from the scenario analysis (result_scenarios.xlsx) and tax credit modeling (result_taxcredits.xlsx).

For each folder/file naming as follows:
./ARMA 

 The Raven input file for synthetic data is labeled as ARMA_train_{Selected Node/Zone}_{Synthetic History Year Configuration}_{segment length}. Historical real-time market data is formatted as {Selected Node/Zone}_realtime_hourly_{year}. The output file folder is formatted as Output_{Input Historical Start Year}_{Input Historical End Year}.

Note: Market data are trained under identical Fourier detrending settings. If specific Fourier modes are added, they are indicated as F{additional added Fourier mode} in output file folders.

./HERON 
The file name follows the following format: <HERONmode>_<ReactorType>_<StorageType>_<MARKET>_<StoragePowerLevel>_<Scenario>.

The transfers.py file contains the necessary functions for calculating duration-specific power and energy costs, as well as the fixed O&M cost for storage.

Note: The HERON input file (sweep_HTGR_LMB_ERC_P100_Base.xml) for the base scenario includes all parameters for scenario analysis commented out (HTGR CAPEX, Fixed O&M, Storage Power Level, Storage Energy Capacity Sweep Range, Storage RTE). Depending on the specific scenario, uncomment the necessary parameters and comment out the currently active ones
