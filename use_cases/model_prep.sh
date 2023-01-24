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
cd train/carbontax
(cd OH && for I in Data_*.csv; do mv $I ${I}.orig; head -n -23 ${I}.orig > $I; done)


