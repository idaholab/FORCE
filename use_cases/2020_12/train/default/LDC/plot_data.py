
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

p = pd.read_csv('./ldc_data.csv', index_col=[0,1,2])[['counts', 'prices']]

ds = xr.Dataset.from_dataframe(p)

fig, ax = plt.subplots()
for sample in ds.RAVEN_sample_ID:
  sample = sample.values
  for year in ds.YEAR.values:
    if year % 5 != 0: continue
    year = year#.values
    sub = ds.sel(RAVEN_sample_ID=sample, YEAR=year)
    counts = sub.counts.values
    prices = sub.prices.values
    first_zero = np.argmax(counts == 0)
    ax.step(counts[:first_zero+1], prices[:first_zero+1]/1000, '.-', where='pre', alpha=1, label=f'{year}') # TODO case?
box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 1, box.height])
ax.legend(bbox_to_anchor=(1.05, 1), ncol=2, borderaxespad=0.)
ax.set_xlabel('Hours exceeding price')
ax.set_ylabel('Electricity price, $/MWh')
fig.savefig('LDC.png')
plt.show()


print('done')
