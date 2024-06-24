import xml.etree.ElementTree as ET
import os
import subprocess
import platform
import shutil


def check_parallel(path) -> bool:
    """
    Checks if a ravenframework input file uses parallel processing. This poses a problem for the executable
    on MacOS and possibly Linux.

    @In, path, str, path to the input file
    @Out, is_parallel, bool, True if parallel processing is used, False otherwise
    """
    is_parallel = False

    tree = ET.parse(path)
    tree.find()

    return is_parallel


def find_workbench():
    """
    Finds the NEAMS Workbench executable
    """
    workbench_path = None
    if platform.system() == "Windows":
        if os.environ.get('WORKBENCH_PATH'):
            workbench_path = os.environ['WORKBENCH_PATH']
        else:
            workbench_path = shutil.which('workbench')
    elif platform.system() == "Darwin":
        # Look in the /Applications directory for a directory starting with "Workbench"
        for app in os.listdir("/Applications"):
            if app.startswith("Workbench") and os.path:
                workbench_path = os.path.join("/Applications", app, "Contents/MacOS/Workbench")
                break
        else:
            print("ERROR: Could not find the NEAMS Workbench application in the /Applications directory. "
                  "Has Workbench been installed?")
    else:  # Linux, not yet supported
        print("Automatic connection of FORCE tools to the NEAMS Workbench is not yet supported on Linux.")
    return workbench_path


def run_in_workbench(file: str | None = None):
    """
    Opens the given file in the NEAMS Workbench
    @ In, file, str, optional, the file to open in NEAMS Workbench
    """
    # Find the workbench executable
    workbench_path = find_workbench()
    if workbench_path is None:
        print("ERROR: Could not find the NEAMS Workbench executable. Please set the "
              "WORKBENCH_PATH environment variable or add it to the system path.")
        raise RuntimeError

    # Open the file in the workbench
    command = workbench_path
    # Currently, we're only able to open the MacOS version of Workbench by opening the app itself.
    # This does not accept a file as an argument, so users will need to open Workbench, then open
    # the desired file manually from within the app.
    if file is not None and platform.system() == "Windows":
        command += ' ' + file

    if platform.system() == "Windows":
        os.system(command)
    elif platform.system() == "Darwin":
        subprocess.call(["/usr/bin/open", "-n", "-a", workbench_path])
    else:
        print("ERROR: Automatic connection of FORCE tools to the NEAMS Workbench is only supported "
              "on Windows and MacOS. Please open Workbench manually and open the desired file.")
