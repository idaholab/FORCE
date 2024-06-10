from typing import Optional
import os
import tkinter as tk
import argparse
from collections import namedtuple

from .file_location_persistence import FileLocationPersistence
from .file_dialog import FileDialogController
from ui.utils import run_in_workbench

class FileSpec:
    """ Input/output file specification for a package. """
    def __init__(self,
                 arg_name: str,
                 description: str,
                 is_output: bool = False,
                 file_type: Optional[str] = None):
        """
        Constructor
        @In, arg_name, str, optional, the argument flag for the file
        @In, description, str, the description of the file
        @In, is_output, bool, optional, whether the file is an output file
        @In, file_type, str, optional, the type of file
        @Out, None
        """
        self.arg_name = arg_name
        self.description = description
        self.is_output = is_output
        self.file_type = file_type

    def add_to_parser(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Adds the file specification to the parser.
        @In, parser, argparse.ArgumentParser, the parser
        @Out, parser, argparse.ArgumentParser, the parser with the file specification added
        """
        # if self.arg_name.startswith('-'):
        #     parser.add_argument(self.arg_name, nargs=1, required=False, help=self.description)
        # else:  # positional argument
        #     parser.add_argument(self.arg_name, nargs='?', help=self.description)
        parser.add_argument(self.arg_name, nargs='?', help=self.description)
        return parser


class FileSelectionController:
    """ Controller for the file selection widget. """
    # Specification for the files that are required for each package. These are used to tie any files
    # passed from the command line to the file selection widget and helps define what file extensions
    # are allowed for each file.
    _file_selection_specs = {
        'teal': [FileSpec('-iXML', 'TEAL XML File', file_type='xml'),
                 FileSpec('-iINP','Variable Inputs File', file_type='txt'),
                 FileSpec('-o', 'Output File', is_output=True)],
        'ravenframework': [FileSpec('filename', 'RAVEN XML File', file_type='xml')],
        'heron': [FileSpec('filename', 'HERON Input File', file_type='xml')]
    }

    def __init__(self, model, view):
        """
        Constructor
        @In, model, Model, the model
        @In, view, FileSelection, the view
        @Out, None
        """
        self.file_selection = view
        self.file_dialog_controllers = {}

        # Remember the file locations for the user
        self.persistence = FileLocationPersistence()

        # Create the file selectors, adding any files specified from the command line
        model_package_name = model.get_package_name().strip().lower()
        self._file_specs = self._file_selection_specs[model_package_name]
        args, self.unknown_args = self._parse_cli_args()
        for spec in self._file_specs:
            # Create a new file selector view based on the file spec
            self.file_selection.new_file_selector(label=spec.description)
            # Create a new file dialog controller for the file selector
            file_dialog_controller = FileDialogController(
                view=self.file_selection.file_selectors[spec.description],
                file_type=spec.file_type,
                is_output=spec.is_output,
                persistence=self.persistence
            )
            if filename := args.get(spec.arg_name, None):
                file_dialog_controller.set_filename(filename)
                self.persistence.set_location(filename)
            self.file_dialog_controllers[spec.description] = file_dialog_controller

        # Set the action for the "Open in Workbench" button
        if model_package_name == "heron":
            workbench_func = lambda: run_in_workbench(self.file_dialog_controllers['HERON Input File'].get_filename())
            self.file_selection.add_open_in_workbench_button(workbench_func)

    def get_sys_args_from_file_selection(self):
        """
        Gets the files selected by the user and returns them as a list along with their
        corresponding argument flags, if any.
        @In, None
        @Out, args, list, a list of files and their corresponding argument flags, if any
        """
        args = []
        for spec in self._file_specs:
            # Get the filename from the file selector
            filename = self.file_dialog_controllers[spec.description].get_filename()
            # Add the filename with its corresponding argument flag to the list
            if not os.path.exists(filename) and spec.arg_name != '-o':
                raise FileNotFoundError(f"File {filename} not found")
            if spec.arg_name.startswith('-'):  # flag argument, include the flag and the argument
                args.extend([spec.arg_name, filename])
            else:  # positional argument, include the argument only
                args.append(filename)
        # Add any unknown arguments to pass along to the model
        args.extend(self.unknown_args)
        return args

    def close_persistence(self):
        """
        Closes the file location persistence
        @In, None
        @Out, None
        """
        self.persistence.close()

    def _parse_cli_args(self):
        """
        Parse arguments provided from the command line
        @In, None
        @Out, args, dict, the parsed arguments
        @Out, unknown, list, the unknown arguments
        """
        parser = argparse.ArgumentParser()
        for spec in self._file_specs:
            parser = spec.add_to_parser(parser)
        # Handling unknown arguments lets use pass additional arguments to the model while only directly
        # handling the file selection arguments.
        args, unknown = parser.parse_known_args()
        args = vars(args)
        # Positional arguments requiring a specific file type may be missing, and an unknown argument
        # may have been interpreted as being that file argument. We'll check if the argument has the
        # correct file extension and if it does, we'll assume it's the file argument. Otherwise, we'll
        # remove it and add it to the list of unknown arguments. Finally, we'll check the unknown arguments
        # and make sure the file argument didn't end up in there.
        for spec in self._file_specs:
            if spec.arg_name not in args:
                for arg in unknown:
                    if arg.endswith(f'.{spec.file_type}'):
                        args[spec.arg_name] = arg
                        unknown.remove(arg)
                        break
        # Any arguments with flags will have had the '-' stripped off. It'll be helpful to know which
        # arguments were specified with flags, so we'll add the '-' back to the keys.
        for key in args.keys():
            if f'-{key}' in [spec.arg_name for spec in self._file_specs]:
                args[f'-{key}'] = args.pop(key)
        return args, unknown
