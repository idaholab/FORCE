Use case for the LWRS M3 milestone (September 30th 2022).

The goal of this TEA (Techno-Economic Analysis) is to demonstrate the economic potential of the co-production of electricity and synthetic fuels (synfuels) for the transportation sector using the existing fleet of LWRs. 

The demonstration will be performed for the Braidwood NPP in the PJM market. The analysis' methodology relies on the comparison of the Net Present Value of different systems to determine which one is the most profitable given a certain market structure. 

The following cases will be run: 
- baseline_elec: LWR, PJM LMP for electricity prices (ARMA model trained on the data for the Braidwood node 2018-2021, assuming a cycle of 4 years); sets the reference NPV
- med_h2_ptc: Main Median case, LWR, 1000 MWe Fischer-Tropsch (FT) and HTSE (High Temperature Steam Electrolysis) synfuel production process, synfuel prices at EIA projection BAU, PJM LMP electricity prices, clean hydrogen PTC from 2022 IRA implemented, co2 feedstock costs from supply curve
- med_h2_ptc_fuel_ptc: Median case with additional synfuel PTC
- med_no_h2_ptc: Median case without h2 PTC
- plant_cap_low: Median case with a 400 MWe synfuel production process
- synfuel_high: Median case with synfuel prices at EIA x1.2
- synfuel_low: Median case with synfuel prices at EIA x0.8
- co2_high: Median case with fixed co2 cost at $75/ton
- co2_low: Median case with fixed co2 cost at $1/ton
- elec_high: Median case with fixed electricity prices at $64.71/MWe (Arizona average)
- elec_low: Median case with fixed electricity prices at $22.98/MWe (ERCOT average)