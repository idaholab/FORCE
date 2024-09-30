#!/bin/bash

# Have users point to the location of their conda installation so we can properly activate the
# conda environment that is being made. Use the "--conda-defs" option to specify this path.
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --conda-defs)
            CONDA_DEFS="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Establish conda environment
conda create -n force_build_310 python=3.10 -y
source $CONDA_DEFS
conda activate force_build_310

# Check that the conda environment is active. If not, exit.
if [[ $CONDA_DEFAULT_ENV != "force_build_310" ]]; then
    echo "Conda environment not activated. Maybe the path to the conda installation is incorrect?"
    echo "Provided conda path: $CONDA_DEFS"
    exit 1
fi

pip install cx_Freeze
pip install raven-framework heron-ravenframework teal-ravenframework
# If on macOS, use conda to install ipopt
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Note: The PyPI version of ipopt is not maintained and is severl major version
    # behind the conda-forge distribution.
    conda install -c conda-forge ipopt -y
fi

# Build the FORCE executables
python setup.py install_exe --install-dir force_install
