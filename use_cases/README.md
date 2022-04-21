# heron_cases

This repository allows a private, central storage for running analysis cases without burdening the public framework repositories.

## File Structure

```
2020                      # Year the case was created.
└── 12                    # Month of the year the case was submitted.
    ├── data              # Relevant data pertaining to the case.
    ├── presentations     # Relevant presentations pertaining to the case.
    ├── reports           # Relevant reports pertaining to the case.
    ├── run               # HERON output and run data
    ├── scripts           # Helper scripts for plotting and automating the case.
    └── train             # ARMA training output and plots.
```

## Helper Scripts

Some scripts have been created to either **a)** help in automating data and plot
outputs for relevant case runs or **b)** to reproduce the required
case-information without pollutting the git history of this repo.

  **raw_data_proc.py** - will take the data provided in `2020/12/data/from_EPRI`
  and place it in the correct ARMA training folder. This should be one of the
  first scripts run when attempting to reproduce the ARMA data.

  ```bash
  $ ./2020/12/scripts/raw_data_proc.py -h
  usage: raw_data_proc.py [-h] [--ln] path

  Raw data processing script for EPRI.

  positional arguments:
    path        Specify which state data to visualize.

  optional arguments:
    -h, --help  show this help message and exit
    --ln        Transform all numerical data using a natural log.
  ```

  **fft_data_proc.py** - will analyze and output a plot of the results from
  running a FFT analysis using Raven. This script will be useful in determining
  proper Fourier bases for a model.

  ```bash
  $ ./2020/12/scripts/fft_data_proc.py -h
  usage: fft_data_proc.py [-h] [-s STATE] [-c CASE]

  FFT Plotting Script for EPRI Data.

  optional arguments:
    -h, --help               show this help message and exit
    -s STATE, --state STATE  Specify which state data to visualize. Default "OH"
    -c CASE, --case CASE     Specify which scenario data to visualize. Default "default"
  ```

  **rom_plots.py** - will create a set of plots that will compare the original
  input data with the sampled ARMA output. The default set of plots created are
  the:

  1. Load duration curve plot
  2. Histogram of ARMA sampled outputs.
  3. Time-Series overlay plot showing sampled ARMA fit.

  There are also a set of _subcommands_ associated with this script:

  1. **extract-xml** - will extract an embedded xml file in a specified png file.
  2. **plot-og** - will plot the fourier decomposition of the orignal time-series.

  ```bash
  $ ./2020/12/scripts/rom_plots.py -h
  usage: rom_plots.py [-h] [-t] [-e] [-s STATE] [-c CASE] {plot-og,extract-xml} ...

  ARMA Plotting Script for EPRI Data

  positional arguments:
    {plot-og, extract-xml}

  optional arguments:
    -h, --help               show this help message and exit
    -t, --add-tables         Add descriptive tables to plot margin.
    -e, --embed-xml          Embed current xml file into image output.
    -s STATE, --state STATE  Specify which state data to visualize.
    -c CASE, --case CASE     Specify which scenario data to visualize.
  ```
