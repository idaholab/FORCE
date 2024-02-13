import sys
from cx_Freeze import setup, Executable, build_exe

import HERON.templates.write_inner

build_exe_options = {
    "packages": ["ravenframework","msgpack","ray","crow_modules","AMSC","sklearn","pyomo","HERON"],
    "includes": ["ray.thirdparty_files.colorama","ray.autoscaler._private","pyomo.common.plugins","HERON.templates.template_driver"],
    "include_files": [(HERON.templates.write_inner.__file__,"lib/HERON/templates/write_inner.py")],
    "include_msvcr": True,
}


setup(
    name="force",
    version="0.1",
    description="FORCE package",
    executables=[Executable(script="raven_framework.py",icon="raven_64.ico"),
                 Executable(script="heron.py",icon="heron_64.ico")],
    options={"build_exe": build_exe_options},
)
