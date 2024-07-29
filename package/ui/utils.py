import sys
import os
import pathlib
import subprocess
import platform
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog


def is_frozen_app() -> bool:
    """
    Infers whether the application being run is a frozen executable or not. This is done by checking the
    location and file extension of the HERON executable.

    @return, bool, True if the application is a frozen executable, False otherwise
    """
    current_file_dir = pathlib.Path(__file__).parent
    # If there's a "heron.py" file one directory up from this file, then we're likely running from the
    # source code. Frozen executables will have "heron" or "heron.exe" as the executable name.
    # FIXME: This is likely to be a bit fragile! Is there a better way to determine if we're running from
    # a frozen executable?
    if (current_file_dir.parent / "heron.py").exists():
        return False
    else:
        return True


def get_workbench_exe_path(workbench_dir: pathlib.Path) -> pathlib.Path:
    """
    Returns the path to the Workbench executable, dependent on the operating system.

    @ In, workbench_dir, pathlib.Path, the path to the Workbench installation directory
    @ Out, workbench_exe_path, pathlib.Path, the path to the Workbench executable
    """
    if platform.system() == "Windows":
        workbench_exe_path = workbench_dir / "bin" / "Workbench.exe"
    elif platform.system() == "Darwin":
        workbench_exe_path = workbench_dir / "Contents" / "MacOS" / "Workbench"
    elif platform.system() == "Linux":
        workbench_exe_path = workbench_dir / "bin" / "Workbench"
    else:
        raise ValueError(f"Platform {platform.system()} is not supported.")

    return workbench_exe_path


def get_workbench_dir_from_exe_path(workbench_exe_path: pathlib.Path) -> pathlib.Path:
    """
    Returns the path to the Workbench installation directory from the path to the Workbench executable.

    @ In, workbench_exe_path, pathlib.Path, the path to the Workbench executable
    @ Out, workbench_dir, pathlib.Path, the path to the Workbench installation directory
    """
    if platform.system() == "Darwin":
        workbench_dir = workbench_exe_path.parent.parent.parent
    else:
        workbench_dir = workbench_exe_path.parent.parent
    return workbench_dir


def verify_workbench_dir(workbench_dir: pathlib.Path) -> bool:
    """
    Verifies that the given path is a valid NEAMS Workbench installation directory. This is done by checking for the Workbench executable,
    dependent on the operating system.

    @ In, workbench_dir, pathlib.Path, the path to the Workbench installation directory
    @ Out, valid, bool, True if the directory is a valid Workbench installation, False otherwise
    """
    workbench_exe_path = get_workbench_exe_path(workbench_dir)
    valid = workbench_exe_path.exists()
    return valid


def get_dirs(dirname: pathlib.Path, pattern: str = "*") -> list[pathlib.Path]:
    """
    Finds all directories in dirname that match the given pattern.

    @ In, dirname, pathlib.Path, the directory to search
    @ In, pattern, str, optional, the pattern to match directories against
    @ Out, dirs, list[pathlib.Path], the list of directories that match the pattern
    """
    dirs = [p for p in dirname.iterdir() if p.is_dir() and p.match(pattern)]
    return dirs


def check_workbench_file_for_dir(workbench_file: pathlib.Path) -> pathlib.Path | None:
    """
    Checks the given .workbench file for the installation directory of Workbench. If file does not exist, None is returned. If
    the file does exist but if the Workbench executable cannot be found there, the WORKBENCHDIR key is deleted and None is returned.
    Finally, if the file exists and the Workbench executable is found, the path to the Workbench installation directory is returned.

    @ In, workbench_file, pathlib.Path, the path to the .workbench file
    @ Out, workbench_dir, pathlib.Path | None, the path to the Workbench installation directory, or None if the file does not exist or the
        Workbench executable cannot be found
    """
    if not workbench_file.exists():  # .workbench file not found at given path
        return None

    # Parse the .workbench file to get the installation directory of Workbench.
    # Info is stored in the format "KEY=VALUE" on each line.
    workbench_config = {}
    with open(workbench_file, 'r') as f:
        for line in f:
            key, value = line.strip().split("=")
            workbench_config[key] = value

    workbench_dir = workbench_config.get("WORKBENCHDIR", None)

    if workbench_dir is not None and not verify_workbench_dir(pathlib.Path(workbench_dir)):
        workbench_dir = None

    if workbench_dir is None:  # either wasn't provided or was invalid
        # If the path in the .workbench file is invalid, delete the WORKBENCHDIR key so we don't keep trying
        # to use it. If no other keys are present, delete the file.
        workbench_config.pop("WORKBENCHDIR", None)  # Remove the key if it exists
        if len(workbench_config) == 0:  # If no other keys are present, delete the file
            workbench_file.unlink()
        else:  # Otherwise, write the updated config back to the file
            with open(workbench_file, 'w') as f:
                for key, value in workbench_config.items():
                    f.write(f"{key}={value}\n")

    return workbench_dir


def find_workbench() -> pathlib.Path | None:
    """
    Finds the NEAMS Workbench executable. A ".workbench" file in the FORCE app's main directory tracks
    the location of the Workbench executable. If that file doesn't exist, we look in common directories
    to find Workbench ourselves. If we still can't find it, we ask the user to locate it manually, if
    desired.

    @ In, None
    @ Out, workbench_exe_path, pathlib.Path | None, the path to the NEAMS Workbench executable, or None if it could not be found
    """
    workbench_path = None

    # Check if a ".workbench" file exists in the main build directory (same directory as the heron and
    # raven_framework executables). That should be 2 directories up from the directory of this file.
    current_file_dir = pathlib.Path(__file__).parent
    # Is this being run from a frozen executable or via the source code? Changes where the package's
    # base directory is located, changing where to look for the .workbench file.
    if is_frozen_app():  # Frozen executable
        workbench_file = current_file_dir.parent.parent / ".workbench"
    else:  # Source code
        workbench_file = current_file_dir.parent / ".workbench"
    workbench_path = check_workbench_file_for_dir(workbench_file)  # Returns None if file doesn't exist or is invalid

    # If that .workbench file doesn't exist, we can look around for the Workbench executable
    if platform.system() == "Windows":
        if wb_path := os.environ.get('WORKBENCH_PATH', None):
            workbench_path = wb_path
        elif wb_path := shutil.which('Workbench'):
            workbench_path = wb_path
        else:
            # Manually search through a few common directories for the Workbench installation
            for path in ["$HOMEDRIVE", "$PROGRAMFILES", "$HOME", "$APPDATA", "$LOCALAPPDATA"]:
                path = pathlib.Path(os.path.expandvars(path))
                if not path.exists():
                    continue
                for loc in get_dirs(path, "Workbench*"):
                    if verify_workbench_dir(loc):
                        workbench_path = loc
                        break
    elif platform.system() == "Darwin":
        # The only place Workbench should be installed on Mac is in the Applications directory.
        for app in get_dirs(pathlib.Path("/Applications"), "Workbench*"):
            if verify_workbench_dir(app):
                workbench_path = app
                break
    # NOTE: Workbench install on Linux is only with a source install which has no standard location. We'll rely on the user to connect
    # the two tools.

    # If we still haven't found Workbench, let the user help us out. Throw up a tkinter warning dialog to
    # ask the user to locate the Workbench executable.
    if workbench_path is None:
        root = tk.Tk()
        root.withdraw()

        response = messagebox.askyesno(
            title="NEAMS Workbench could not be found!",
            message="The NEAMS Workbench executable could not be found. Would you like to manually find the Workbench installation directory?"
        )
        if response:
            dialog_title = "Select NEAMS Workbench Application" if platform.system() == "Darwin" else "Select NEAMS Workbench Directory"
            workbench_path = filedialog.askdirectory(title=dialog_title)
            if workbench_path:
                is_valid = verify_workbench_dir(pathlib.Path(workbench_path))
                if not is_valid:
                    messagebox.showerror(
                        title="Invalid Workbench Directory",
                        message="The NEAMS Workbench executable was not found in the selected directory!"
                    )
                    workbench_path = None
                else:
                    with open(workbench_file, 'w') as f:
                        f.write("WORKBENCHDIR=" + workbench_path)

    if workbench_path is None:  # If we still don't have a valid path, just give up I guess
        return None

    if isinstance(workbench_path, str):
        workbench_path = pathlib.Path(workbench_path)

    workbench_exe_path = get_workbench_exe_path(workbench_path)

    return workbench_exe_path


def create_workbench_heron_default(workbench_dir: pathlib.Path):
    """
    Creates a configuration file for Workbench so it knows where HERON is located.

    @ In, workbench_dir, pathlib.Path, the path to the NEAMS Workbench installation directory
    @ Out, NOne
    """
    # First, we need to find the HERON executable. This will be "heron.exe" on Windows
    # and just "heron" on MacOS and Linux. It should be located 2 directories up from the
    # directory of this file.
    current_file_dir = pathlib.Path(__file__).parent

    # Is this a frozen executable or source code? Changes where the package's base directory is located.
    if (current_file_dir.parent / "heron.py").exists():  # Source code
        heron_path = current_file_dir.parent.parent / "heron.py"
    else:  # Frozen executable
        heron_path = current_file_dir.parent.parent / "heron"
        # Windows executables have a ".exe" extension
        if platform.system() == "Windows":
            heron_path = heron_path.with_suffix(".exe")

    # If the HERON executable doesn't exist, we can't create the Workbench configuration file
    if not heron_path.exists():
        print(f"ERROR: Could not find the HERON executable in the directory {heron_path.parent}.")
        return

    # Create the configuration file for Workbench
    workbench_config_file = workbench_dir / "default.apps.son"
    if workbench_config_file.exists():
        # If the default app config file already exists, don't overwrite it.
        print("Workbench default.apps.son file already exists! No edits made.")
        return

    # If the file doesn't exist, create it and add a configuration for HERON
    print("Adding HERON configuration to NEAMS Workbench", workbench_config_file)
    with open(workbench_config_file, "w") as f:
        f.write("applications {\n"
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


def convert_xml_to_heron(xml_file: pathlib.Path, workbench_path: pathlib.Path) -> pathlib.Path:
    """
    Converts an .xml file to a .heron file using Workbench's xml2eddi.py conversion script.

    @ In, xml_file, pathlib.Path, the path to the .xml file to convert
    @ In, workbench_path, pathlib.Path, the path to the Workbench installation directory
    @ Out, heron_file, pathlib.Path, the path to the converted .heron file
    """
    # Find the xml2eddi.py script in the Workbench installation directory
    xml2eddi_script = workbench_path / "rte" / "util" / "xml2eddi.py"
    if not xml2eddi_script.exists():
        print("ERROR: Could not find the xml2eddi.py script in the Workbench installation directory.")
        return None

    # Convert the .xml file to a .heron file by running the xml2eddi.py script with the .xml file as
    # an argument and redirecting the output to a .heron file with the same name.
    heron_file = xml_file.with_suffix(".heron")
    with open(heron_file, "w") as f:
        subprocess.run(["python", str(xml2eddi_script), str(xml_file)], stdout=f)

    return heron_file


def run_in_workbench(file: str | None = None):
    """
    Opens the given file in the NEAMS Workbench
    @ In, file, str, optional, the file to open in NEAMS Workbench
    """
    # Find the Workbench executable
    workbench_path = find_workbench()
    if workbench_path is None:
        print("ERROR: Could not find the NEAMS Workbench executable. Please set the "
              "WORKBENCH_PATH environment variable, add it to the system path, or specify it manually "
              "with the WORKBENCHDIR key in the \".workbench\" file in the main FORCE directory.")
        return

    # Create Workbench default configuration for HERON if a default configurations file does not exist
    workbench_install_dir = get_workbench_dir_from_exe_path(workbench_path)
    create_workbench_heron_default(workbench_install_dir)

    # Convert the .xml file to a .heron file if one was provided
    if file is not None:
        file = pathlib.Path(file)
        if not file.exists():
            print(f"ERROR: The file {file} does not exist.")
            return

        if file.suffix == ".xml":
            heron_file = convert_xml_to_heron(file, workbench_install_dir)
            if heron_file is None:
                return
            file = heron_file
        file = str(file)

    # Open the file in Workbench
    # Currently, we're only able to open the MacOS version of Workbench by opening the app itself.
    # This does not accept a file as an argument, so users will need to open Workbench, then open
    # the desired file manually from within the app.
    command = str(workbench_path)
    # if file is not None and platform.system() == "Windows":
    #     command += ' ' + file

    print("Opening Workbench...", file=sys.__stdout__)
    print("***If this is the first time you are running Workbench, this may take a few minutes!***\n", file=sys.__stdout__)
    if platform.system() == "Windows":
        subprocess.run([command, file])
    else:
        # NOTE: untested on Linux as of 2024-07-22
        subprocess.run(["/usr/bin/open", "-n", "-a", workbench_path])
