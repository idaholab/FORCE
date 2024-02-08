import sys
import os
from cx_Freeze import setup, Executable, build_exe

import HERON.templates.write_inner


netCDF4_libs_path = os.path.join(os.path.dirname(sys.executable), "lib", "site-packages", "netCDF4.libs")

build_exe_options = {
    "packages": ["ravenframework","msgpack","ray","crow_modules","AMSC","sklearn","pyomo","HERON", "pyarrow", "netCDF4", "cftime"],
    "includes": ["ray.thirdparty_files.colorama","ray.autoscaler._private","pyomo.common.plugins","HERON.templates.template_driver"],
    "include_files": [(HERON.templates.write_inner.__file__,"lib/HERON/templates/write_inner.py"),
                      ("Ipopt-3.14.13-win64-msvs2019-md/","local/bin/Ipopt-3.14.13-win64-msvs2019-md"),
                      (netCDF4_libs_path,"lib/netCDF4")],
    "include_msvcr": True
}


setup(
    name="force",
    version="0.1",
    description="FORCE package",
    executables=[Executable("raven_framework.py"),Executable("heron.py")],
    options={"build_exe": build_exe_options},
)
