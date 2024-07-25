import sys
import platform
import os
import pathlib
from cx_Freeze import setup, Executable, build_exe

import HERON.templates.write_inner


build_exe_options = {
    "packages": ["ravenframework","msgpack","ray","crow_modules","AMSC","sklearn","pyomo","HERON","TEAL","pyarrow","netCDF4","cftime","distributed","dask","tensorflow"],
    "includes": ["ray.thirdparty_files.colorama","ray.autoscaler._private","pyomo.common.plugins","HERON.templates.template_driver","dask.distributed","imageio.plugins.pillow","imageio.plugins.pillowmulti","imageio.plugins.pillow_info"],
    "include_files": [(HERON.templates.write_inner.__file__,"lib/HERON/templates/write_inner.py")],
}

# Add all of the HERON template XML files to the build
write_inner_path = pathlib.Path(HERON.templates.write_inner.__file__)
for xml_file in os.listdir(write_inner_path.parent):
    if xml_file.endswith(".xml"):
        build_exe_options["include_files"].append((write_inner_path.parent / xml_file, f"lib/HERON/templates/{xml_file}"))

# Some files must be included manually for the Windows build
if platform.system().lower() == "windows":
    # netCDF4 .dll files get missed by cx_Freeze
    # ipopt executable must be included manually
    netCDF4_libs_path = os.path.join(os.path.dirname(sys.executable), "lib", "site-packages", "netCDF4.libs")
    build_exe_options["include_files"] += [
        #("Ipopt-3.14.13-win64-msvs2019-md/","local/bin/Ipopt-3.14.13-win64-msvs2019-md"),  # FIXME: Point to the correct location for ipopt executable
        (netCDF4_libs_path,"lib/netCDF4")
    ]
    # Include the Microsoft Visual C++ Runtime
    build_exe_options["include_msvcr"] = True
else:
    ipopt_path = os.path.join(os.path.dirname(sys.executable), "ipopt")
    build_exe_options["include_files"] += [
       (ipopt_path, "local/bin/ipopt")
    ]

setup(
    name="force",
    version="0.1",
    description="FORCE package",
    executables=[Executable(script="raven_framework.py",icon="raven_64.ico"),
                 Executable(script="heron.py",icon="heron_64.ico"),
                 Executable(script="teal.py",icon="teal_64.ico")],
    options={"build_exe": build_exe_options},
)
