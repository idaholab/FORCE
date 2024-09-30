# FORCE One-Step Installer Creation
FORCE one-step installers are created using the `cx_Freeze` python package after creating a python environment using either `venv` or `conda`.
A computer with the same operating system and architecture as the target operating system must be used to generate an installer, i.e. use a Windows machine to generate a Windows installer, a Mac (Intel) to generate a Mac installer, etc.
Note that installers generated with Apple computers with M-series chips will not be backwards compatible with Intel-based Apple computers.

Windows and macOS are the only operating systems currently supported.
Linux users are encouraged to use pip-installed or source built versions of the RAVEN, HERON, and TEAL software packages.

## 1. Build FORCE executables
Create a conda environment `force_build_310`, install the RAVEN, HERON, and TEAL pip packages, and build the FORCE executables using the script
```console
./build_force.sh
```

## 2. Add IPOPT to build directory (Windows only)
Download the IPOPT Windows binary:
https://github.com/coin-or/Ipopt/releases

Extract the downloaded zip directory and copy its contents to the raven_install directory, ensuring to replace the version numbers of IPOPT as needed.
```console
cd force_install
unzip ~/Downloads/Ipopt-3.14.12-win64-msvs2019-md.zip
mv Ipopt-3.14.12-win64-msvs2019-md local
cd ..
```

## 3. Copy examples and build/copy the RAVEN, HERON, and TEAL documentation
Adding examples and documentation to the one-step installer requires having the source installation present on the build machine, with the `raven_libraries` conda environment already created.
```console
conda activate raven_libraries
./copy_examples.sh --raven-dir /path/to/raven --heron-dir /path/to/HERON
cp -R examples force_install/examples
./make_docs.sh --raven-dir /path/to/raven --heron-dir /path/to/HERON --teal-dir /path/to/TEAL
cp -R docs force_install/docs
```
When running the `make_docs.sh` script, the optional `--no-build` flag may be added if the desired documentation PDFs have already been built, and you do not wish to rebuild the documents.

## 4. Get NEAMS Workbench installer
The installers for the NEAMS Workbench software can be found here:
https://code.ornl.gov/neams-workbench/downloads/-/tree/5.4.1?ref_type=heads

Download `Workbench-5.4.1.exe` for Windows and `Workbench-5.4.1.dmg` for macOS.
Place this file in the current directory.

Windows:
```console
cp ~/Downloads/Workbench-5.4.1.exe .
```

macOS:
```console
cp ~/Downloads/Workbench-5.4.1.dmg .
```

## 5. Create the installer
### Windows
The Windows installer is created using Inno Setup.
Run the `inno_package.iss` script from the Inno Setup application.
The resulting .exe installer file can be found in the `inno_output` directory.

### macOS
Run the macOS build script
```console
./build_mac_app.sh
```
The disk image `FORCE.dmg` contains applications for both FORCE and Workbench.
