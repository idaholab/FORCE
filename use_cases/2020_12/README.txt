
Cases for M2 HERON Milestone due 2020-12-15.

PI: Paul Talbot
Project Contact: Cristian Rabiti
Contributors: Dylan McDowell, James Richards

Data for the load (in many different breakdowns) as well as marginal price
 and capacity evolution every 5 years for 40 electricity technologies was
provided by EPRI for 6 different cases using US-REGEN (for 2 states, but we
focused on IL for this analysis):

Policy: Nominal, CarbonTax, RPS
Pricing: Default, LNHR

Note Default and Nominal are only different names to help distinguish cases.

The data from EPRI is provided in excel spreadsheets under ./data/from_EPRI.
To turn these cases into trainable signals, use ./scripts/raw_data_proc.py
targetting the excel sheet of the case you want to train. This requires the
python library xlrd to be available (it's on conda).

The ARMA training algorithms are in ./train by case. Any cases must have an
ARMA trained before they can be run.

To run the cases, run ./run/write_cases.py, which populated the regulated and
deregulated cases using the dereg_template.xml and reg_template.xml. Then
navigate into any folder (for which there's trained ARMAs) and run HERON on
the generated XML file. Then run RAVEN on the generated outer.xml, tweaking
any cluster run parameters desired first.

The operating branches for this analysis:
RAVEN: arma_eval_pk on PaulTalbot-INL/raven
HERON: milestone_changes on PaulTalbot-INL/HERON
