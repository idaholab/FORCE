# New York Default Case

After cloning this repo, specific files will be missing that you'll need to add via
scripts provided in this repository. Before running the scripts mentioned above, please
ensure you have your RAVEN conda environment activated and have installed the
required packages:

```bash
conda activate raven_libraries
# If you want to run the plotting and other helper scripts install these libraries
conda install cryptography openpyxl
```

See the [RAVEN Wiki](https://github.com/idaholab/raven/wiki/installationMain) for
more details on setting up RAVEN.

Upon cloning, the `Output` folder should look like:

```
Output
└── Data.csv
```

To get the required data stored in the `Output` folder, run the following command:

```bash
# Relative file paths assuming you are in heron_cases/2021/12/train/ny_default_load
../../scripts/raw_data_proc.py ../data/from_EPRI/NY_Default_Load.xlsx
```

This script will process, clean, and store the requisite data in the `Output` folder. The
`Output` folder should now contain the following files:

```
Output
├── Data.csv
└── Data_0.csv
```

Note that the new files contain data specified by total demand, wind generation, and solar generation (e.g.`Data\_0.csv`).

You are now able to train a synthetic history by running RAVEN:

```bash
<path/to/raven>/raven_framework ny_default_load_train.xml
```

If training was successful, you should see a message at the bottom of the output that reads something like:

```
--------------------------------------------------
There were 1 warnings during the simulation run:
(1 time) Nothing to write to CSV! Checking metadata ...
--------------------------------------------------
(  227.16 sec) SIMULATION               : Message         -> Run complete!
```

If there were errors, please take a moment to scroll through the RAVEN output and diagnose the problem.

Your `Output` folder should now contain the following files:

```
Output
├── Data.csv
├── Data_0.csv
├── romMeta.xml
├── arma.pk
└── synth.csv
```

Note the addition of the `arma.pk` file. HERON will reference that file in its'
input files contained in the `heron_cases/2021/12/run` directory.

Also, note the `synth.csv` This is a sampled manifestation of our ARMA model. This
data will be used in the following plotting script.

You can get a visual diagnosis of the model by now running the provided plotting
script, `rom_plots.py`. You can do this by running the following command in your terminal:

```bash
# Relative file paths assuming you are in heron_cases/2021/12/train/ny_default_load
../../scripts/rom_plots.py ny_default_load_train.xml
```
