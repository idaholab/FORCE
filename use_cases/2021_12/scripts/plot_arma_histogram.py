#!/usr/bin/env python
"""
"""
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

CASE_DICT = {('Reference', 'No_Storage'): {'coeffs': (12.791, 0.025),
                                           'windcap': 10.435570,
                                           'solarcap': 14.894274,
                                           'nucap': 1.143500},

              ('Reference', 'Storage'):    {'coeffs': (12.881, 0.026),
                                            'windcap': 10.435570,
                                            'solarcap': 14.289311,
                                            'nucap': 1.143500},

              ('CES', 'No_Storage'):       {'coeffs': (12.403, 0.032),
                                            'windcap': 11.881869,
                                            'solarcap': 9.774715,
                                            'nucap': 5.242805},

              ('CES', 'Storage'):          {'coeffs': (12.791, 0.034),
                                            'windcap': 9.774715,
                                            'solarcap': 11.881870,
                                            'nucap': 5.242805}}


def main():
    """
    """
    test_path = Path('../train/ny_default_load/Output/synth.csv')
    test_df = pd.read_csv(test_path)
    test_df['WIND_G'] = test_df['WIND'] * CASE_DICT[('Reference','No_Storage')]['windcap']
    test_df['SOLAR_G'] = test_df['SOLAR'] * CASE_DICT[('Reference','No_Storage')]['solarcap']
    test_df['VRE'] = test_df['WIND_G'] + test_df['SOLAR_G']
    test_df['NETLOAD'] = test_df['TOTALLOAD'] - test_df['VRE']

    print(test_df)

    plt.hist(test_df['NETLOAD'], bins=30)


if __name__ == '__main__':
    main()
