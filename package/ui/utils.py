import os
import pathlib
import subprocess
import platform
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog


def find_workbench() -> pathlib.Path:
    """
    Finds the NEAMS Workbench executable. A ".workbench" file in the FORCE app's main directory tracks
    the location of the Workbench executable. If that file doesn't exist, we look in common directories
    to find Workbench ourselves. If we still can't find it, we ask the user to locate it manually, if
    desired.
    """
    workbench_path = None

    # Check if a ".workbench" file exists in the main build directory (same directory as the heron and
    # raven_framework executables). That should be 2 directories up from the directory of this file.
    current_file_dir = pathlib.Path(__file__).parent
    workbench_file = current_file_dir.parent.parent / ".workbench"
    workbench_file_exists = workbench_file.exists()
    if workbench_file_exists:
        with open(workbench_file, 'r') as f:
            workbench_path = f.read().strip()
            if not os.path.exists(workbench_path):
                # If the path in the .workbench file is invalid, delete the file so we don't keep trying
                # to use it.
                workbench_path = None
                os.remove(workbench_file)
            else:
                return workbench_path

    # If that .workbench file doesn't exist, we can look around for the Workbench executable
    if platform.system() == "Windows":
        if wb_path := os.environ.get('WORKBENCH_PATH', None):
            workbench_path = wb_path
        elif wb_path := shutil.which('Workbench'):
            workbench_path = wb_path
        else:
            # Manually search through a few common directories for the Workbench installation
            for path in ["$HOMEDRIVE\\", "$PROGRAMFILES", "$HOME", "$APPDATA", "$LOCALAPPDATA"]:
                path = os.path.expandvars(path)
                if not os.path.exists(path):
                    continue
                for file in os.listdir(path):
                    if file.startswith("Workbench"):
                        wb_path = os.path.join(path, file, "bin", "Workbench.exe")
                        if os.path.exists(wb_path):
                            workbench_path = wb_path
                            break
    elif platform.system() == "Darwin":
        # Look in the /Applications directory for a directory starting with "Workbench"
        for app in os.listdir("/Applications"):
            if app.startswith("Workbench") and os.path:
                workbench_path = os.path.join("/Applications", app, "Contents/MacOS/Workbench")
                break

    # If we still haven't found Workbench, let the user help us out. Throw up a tkinter warning dialog to
    # ask the user to locate the Workbench executable.
    if workbench_path is None:
        root = tk.Tk()
        root.withdraw()

        response = messagebox.askyesno(
            "NEAMS Workbench could not be found!",
            "The NEAMS Workbench executable could not be found. Would you like to locate it manually?"
        )
        if response:
            workbench_path = filedialog.askopenfilename(
                title="Locate NEAMS Workbench",
                filetypes=[("Workbench Executable", "*.exe")]
            )
            if workbench_path:
                with open(workbench_file, 'w') as f:
                    f.write(workbench_path)

    if isinstance(workbench_path, str):
        workbench_path = pathlib.Path(workbench_path)

    return workbench_path


def create_workbench_heron_default(workbench_path: pathlib.Path):
    """
    Creates a configuration file for Workbench so it knows where HERON is located.
    @ In, workbench_path, pathlib.Path, the path to the NEAMS Workbench executable
    """
    # First, we need to find the HERON executable. This will be "heron.exe" on Windows
    # and just "heron" on MacOS and Linux. It should be located 2 directories up from the
    # directory of this file.
    current_file_dir = pathlib.Path(__file__).parent
    heron_path = current_file_dir.parent.parent / "heron"
    if platform.system() == "Windows":
        heron_path = heron_path.with_suffix(".exe")
    # If the HERON executable doesn't exist, we can't create the Workbench configuration file
    if not heron_path.exists():
        print(f"ERROR: Could not find the HERON executable in the directory {heron_path.parent}.")
        return

    # Create the configuration file for Workbench
    workbench_root_dir = workbench_path.parent.parent
    workbench_config_file = workbench_root_dir / "default.apps.son"
    if workbench_config_file.exists():
        # File already exists, but does a HERON entry already exist? See if HERON mentioned in the
        # file. This isn't as robust as actually parsing the file, but it should work for now.
        with open(workbench_config_file, 'r') as f:
            for line in f:
                if "heron" in line.lower():
                    return
    # If the file doesn't exist or doesn't mention HERON, we need to add it
    print("Adding HERON configuration to NEAMS Workbench", workbench_config_file)
    with open(workbench_config_file, 'a') as f:
        f.write("\napplications {\n"
                "  HERON {\n"
                "    configurations {\n"
                "      default {\n"
                "        options {\n"
                "          shared {\n"
                f"            \"Executable\"=\"{heron_path}\"\n"
                "          }\n"
                "        }\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "}\n")


def run_in_workbench(file: str | None = None):
    """
    Opens the given file in the NEAMS Workbench
    @ In, file, str, optional, the file to open in NEAMS Workbench
    """
    # Find the Workbench executable
    workbench_path = find_workbench()
    if workbench_path is None:
        print("ERROR: Could not find the NEAMS Workbench executable. Please set the "
              "WORKBENCH_PATH environment variable or add it to the system path.")
        raise RuntimeError

    # Point Workbench to the HERON executable if it's not already configured
    create_workbench_heron_default(workbench_path)

    # Open the file in Workbench
    # Currently, we're only able to open the MacOS version of Workbench by opening the app itself.
    # This does not accept a file as an argument, so users will need to open Workbench, then open
    # the desired file manually from within the app.
    command = str(workbench_path)
    if file is not None and platform.system() == "Windows":
        command += ' ' + file

    if platform.system() == "Windows":
        os.system(command)
    elif platform.system() == "Darwin":
        subprocess.call(["/usr/bin/open", "-n", "-a", workbench_path])
    else:
        print("ERROR: Automatic connection of FORCE tools to the NEAMS Workbench is only supported "
              "on Windows and MacOS. Please open Workbench manually and open the desired file.")
