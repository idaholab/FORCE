import sys
import platform
import os
from cx_Freeze import setup, Executable, build_exe

import HERON.templates.write_inner


build_exe_options = {
    "packages": ["ravenframework","msgpack","ray","crow_modules","AMSC","sklearn","pyomo","HERON", "pyarrow", "netCDF4", "cftime"],
    "includes": ["ray.thirdparty_files.colorama","ray.autoscaler._private","pyomo.common.plugins","HERON.templates.template_driver"],
    "include_files": [(HERON.templates.write_inner.__file__,"lib/HERON/templates/write_inner.py")],
}

# Some files must be included manually for the Windows build
if platform.system().lower() == "windows":
    # netCDF4 .dll files get missed by cx_Freeze
    # ipopt executable must be included manually
    netCDF4_libs_path = os.path.join(os.path.dirname(sys.executable), "lib", "site-packages", "netCDF4.libs")
    build_exe_options["include_files"] += [
        ("Ipopt-3.14.13-win64-msvs2019-md/","local/bin/Ipopt-3.14.13-win64-msvs2019-md"),  # FIXME: Point to the correct location for ipopt executable
        (netCDF4_libs_path,"lib/netCDF4")
    ]
    # Include the Microsoft Visual C++ Runtime
    build_exe_options["include_msvcr"] = True


setup(
    name="force",
    version="0.1",
    description="FORCE package",
    executables=[Executable("raven_framework.py"),Executable("heron.py")],
    options={"build_exe": build_exe_options},
)
