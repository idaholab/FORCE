
Creating package way 1:

python3.10 -m venv test310
source test310/bin/activate
pip install cx_Freeze
pip install raven-framework teal-ravenframework heron-ravenframework


python setup.py install_exe --install-dir raven_install


Way 2:

conda create -n test39 python=3.9
conda activate test39

pip install cx_Freeze
pip install raven-framework teal-ravenframework heron-ravenframework

python setup.py install_exe --install-dir raven_install
