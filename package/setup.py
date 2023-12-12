import sys
from cx_Freeze import setup, Executable, build_exe

build_exe_options = {
    "packages": ["ravenframework","msgpack","ray","crow_modules","AMSC","sklearn"],
    "includes": ["ray.thirdparty_files.colorama","ray.autoscaler._private"],
    "include_msvcr": True,
}


setup(
    name="force",
    version="0.1",
    description="FORCE package",
    executables=[Executable("raven_framework.py")],
    options={"build_exe": build_exe_options},
)
