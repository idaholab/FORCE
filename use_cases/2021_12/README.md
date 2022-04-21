# How to Run These Cases


## Generate Synthetic Histories

First, you'll need to generate the synthetic histories required by HERON. There
are two `arma.pk` files that will need to be generated. The respective input file and
README directions on how to generate the required data can be found at:

1. [./train/ny\_default\_load](./train/ny_default_load)
2. [./train/ny\_ces\_load](./train/ny_ces_load)

After completing this step you can move on to running HERON.

## Run HERON

All of the HERON input files can be found in the `run/` folder. To replicate the
results of the 2021 study you'll need to run the following cases:

1. [./run/default](./run/default)
2. [./run/default\_storage](./run/default_storage)
3. [./run/ces](./run/ces)
4. [./run/ces\_storage](./run/ces_storage)


You will also need to run the baseline cases to get a benchmark to compare
against:

1. [./run/default\_baseline](./run/default_baseline)
2. [./run/default\_storage\_baseline](./run/default_storage_baseline)
3. [./run/ces\_baseline](./run/ces_baseline)
4. [./run/ces\_storage\_baseline](./run/ces_storage_baseline)

For example, if you wanted to run the default case. You would navigate to
`run/default` and then run the following commands in your terminal:

```bash
# Paths assuming you are in heron_cases/2021/run/default
<path/to/HERON>/heron default.xml
```

This script will generate a few files:

1. `outer.xml` - a RAVEN input file for the outer optimizaton loop.
2. `inner.xml` - a RAVEN input file for the inner optimizaton loop.
3. `cash.xml` - a RAVEN input file containing additional cashflow information.
4. `heron.lib` - a library required by RAVEN
5. `write_inner.py` a python script used in the inner loop.

__NOTE__: If you are trying to run HERON in parallel on an HPC cluster ensure that
the following XML block can be found inside the `<RunInfo>` block in `outer.xml`:

```xml
<batchSize>7</batchSize>
<internalParallel>True</internalParallel>
<mode>mpi
  <runQSUB/>
</mode>
<expectedTime>72:0:0</expectedTime>
<clusterParameters>-P thermal -j oe</clusterParameters>
```

If you are running on your local computer you can replace these settings with
`<batchSize>1</batchSize>`. Be aware that these HERON runs are quite
computationally expensive and without utilizing parallel computation the runs will
take a long time.

__NOTE__: You can also modify `outer.xml` to tweak initial starting values and
optimizer settings. As this repository stands, that shouldn't be neccesary.

Once all the files have been generated and checked, you can now launch the process
by running the following command:

```bash
<path/to/RAVEN>/raven_framework outer.xml
```

You can check the status of the current run by looking at the latest `out~inner`
files nested inside the working directory specified in the HERON input file. This
file will often contain information on failed runs.

Once the run is complete the results will be contained inside the specified
working directory with the name: `opt_soln_0.csv`. You can compare these results
with the results found in the `gold/` directory.

These steps can then be replicated for the other cases in the 2021 study.
