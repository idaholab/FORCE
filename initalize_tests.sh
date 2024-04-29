#!/bin/bash

git submodule init raven
git submodule init HERON
git submodule update

cd raven

git submodule init plugins/TEAL/
git submodule update

python scripts/install_plugins.py -s plugins/TEAL
python scripts/install_plugins.py -s ../HERON/

./scripts/establish_conda_env.sh --install
./build_raven 

(source ./scripts/establish_conda_env.sh --load && conda install -y -c conda-forge openpyxl)
