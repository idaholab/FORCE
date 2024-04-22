#!/bin/bash

git clone https://github.com/idaholab/raven.git
git clone https://github.com/idaholab/HERON.git

cd raven

git submodule init plugins/TEAL/
git submodule update

python scripts/install_plugins.py -s plugins/TEAL
python scripts/install_plugins.py -s ../HERON/

./scripts/establish_conda_env.sh --install
./build_raven 

(source ./scripts/establish_conda_env.sh --load && conda install -y -c conda-forge openpyxl)
