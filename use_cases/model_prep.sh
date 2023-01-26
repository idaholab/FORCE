#!/bin/bash

SCRIPT_NAME=`readlink $0`
if test -x "$SCRIPT_NAME";
then
    SCRIPT_DIRNAME=`dirname $SCRIPT_NAME`
else
    SCRIPT_DIRNAME=`dirname $0`
fi
SCRIPT_DIR=`(cd $SCRIPT_DIRNAME; pwd)`


#Note, conda should be in path
conda install -y xlrd=1
cd $SCRIPT_DIR/2020_12

./scripts/raw_data_proc.py data/from_EPRI/Carbontax.xlsx
(cd train/carbontax/OH && for I in Data_*.csv; do mv $I ${I}.orig; head -n -23 ${I}.orig > $I; done)

./scripts/raw_data_proc.py data/from_EPRI/Default.xlsx
(cd train/default/OH && for I in Data_*.csv; do mv $I ${I}.orig; head -n -23 ${I}.orig > $I; done)

./scripts/raw_data_proc.py data/from_EPRI/rps.xlsx
(cd train/rps/OH && for I in Data_*.csv; do mv $I ${I}.orig; head -n -23 ${I}.orig > $I; done)

./scripts/raw_data_proc.py data/from_EPRI/Default_LNHR.xlsx
(cd train/default_lnhr/OH && for I in Data_*.csv; do mv $I ${I}.orig; head -n -23 ${I}.orig > $I; done)

./scripts/raw_data_proc.py data/from_EPRI/Carbontax_LNHR.xlsx
(cd train/carbontax_lnhr/OH  && for I in Data_*.csv; do mv $I ${I}.orig; head -n -23 ${I}.orig > $I; done)

./scripts/raw_data_proc.py data/from_EPRI/rps_LNHR.xlsx
(cd train/rps_lnhr/OH  && for I in Data_*.csv; do mv $I ${I}.orig; head -n -23 ${I}.orig > $I; done)
