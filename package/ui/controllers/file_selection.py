from typing import Optional
import os
import tkinter as tk
import argparse
from collections import namedtuple


class FileSpec:
    """ Input/output file specification for a package. """
    def __init__(self,
                 arg_name: str,
                 description: str,
                 default_filename: Optional[str] = None,
                 is_output: bool = False,
                 file_type: Optional[str] = None):
        """
        Constructor
        @In, arg_name, str, optional, the argument flag for the file
        @In, description, str, the description of the file
        @In, default_filename, str, optional, the default filename
        @In, is_output, bool, optional, whether the file is an output file
        @In, file_type, str, optional, the type of file
        @Out, None
        """
        self.arg_name = arg_name
        self.description = description
        self.default_filename = default_filename
        self.is_output = is_output
        self.file_type = file_type

    def add_to_parser(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Adds the file specification to the parser.
        @In, parser, argparse.ArgumentParser, the parser
        @Out, parser, argparse.ArgumentParser, the parser with the file specification added
        """
        parser.add_argument(self.arg_name, nargs=1, required=False, default=self.default_filename,
                            help=self.description)
        return parser


class FileSelectionController:
    """ Controller for the file selection widget. """
    _file_selection_specs = {
        'teal': [FileSpec('-iXML', 'XML File', file_type='xml'),
                 FileSpec('-iINP','CashFlow File'),
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

        # Create the file selectors, adding any files specified from the command line
        model_package_name = model.get_package_name().strip().lower()
        self._file_specs = self._file_selection_specs[model_package_name]
        cli_args = self._parse_cli_args()
        for spec in self._file_specs:
            filename = cli_args.get(spec.arg_name, spec.default_filename)
            if isinstance(filename, (list, tuple)):  # argparse returns items in a tuple sometimes
                filename = filename[0]
            self.file_selection.add_file_selector(spec.description, filename, spec.file_type, spec.is_output)

    def get_files(self):
        """
        Gets the files selected by the user and returns them as a list along with their
        corresponding argument flags, if any.
        @In, None
        @Out, files, list, a list of files and their corresponding argument flags, if any
        """
        files = []
        for spec in self._file_specs:
            # Get the filename from the file selector
            filename = self.file_selection.file_selectors[spec.description].get_filename()
            # Add the filename with its corresponding argument flag to the list
            if not os.path.exists(filename) and spec.arg_name != '-o':
                raise FileNotFoundError(f"File {filename} not found")
            if spec.arg_name.startswith('-'):  # flag argument
                files.extend([spec.arg_name, filename])
            else:  # positional argument
                files.append(filename)
        return files

    def _parse_cli_args(self) -> dict[str]:
        """
        Parse arguments provided from the command line
        @In, None
        @Out, args, dict, the parsed arguments
        """
        parser = argparse.ArgumentParser()
        for spec in self._file_specs:
            parser = spec.add_to_parser(parser)
        args = vars(parser.parse_args())
        # Any arguments with flags will have had the '-' stripped off. It'll be helpful to know which
        # arguments were specified with flags, so we'll add the '-' back to the keys.
        for key in list(args.keys()):
            if f'-{key}' in [spec.arg_name for spec in self._file_specs]:
                args[f'-{key}'] = args.pop(key)
        return args
