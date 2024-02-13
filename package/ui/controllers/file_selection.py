from typing import Optional
import os
import tkinter as tk
import argparse


class FileSelectionController:
    """ Controller for the file selection widget. """
    _file_selection_spec = {
        # package: [(argument flag, file description, default filename)]
        'teal': [('-iXML', 'XML File', None), ('-iINP', 'CashFlow File', None), ('-o', 'Output File', 'teal.out')],
        'ravenframework': [('filename', 'RAVEN XML File', None)],
        'heron': [('filename', 'HERON XML File', None)]
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
        self._files_spec = self._file_selection_spec[model_package_name]
        cli_args = self._parse_cli_args()
        for arg_name, file_title, default in self._files_spec:
            filename = cli_args.get(arg_name, default)
            if isinstance(filename, (list, tuple)):
                filename = filename[0]
            self.file_selection.add_file_selector(file_title, filename)

    def get_files(self):
        """
        Gets the files selected by the user and returns them as a list along with their
        corresponding argument flags, if any.
        @In, None
        @Out, files, list, a list of files and their corresponding argument flags, if any
        """
        files = []
        for arg_name, file_title, _ in self._files_spec:
            # Get the filename from the file selector
            filename = self.file_selection.file_selectors[file_title].get_filename()
            # Add the filename with its corresponding argument flag to the list
            if not os.path.exists(filename) and arg_name != '-o':
                raise FileNotFoundError(f"File {filename} not found")
            if arg_name.startswith('-'):  # flag argument
                files.extend([arg_name, filename])
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
        for arg, description, default in self._files_spec:
            nargs = '?' if arg == 'filename' else 1  # filename is an optional positional argument
            parser.add_argument(arg, nargs=nargs, required=False, default=default, help=description)
        args = vars(parser.parse_args())
        # Any arguments with flags will have had the '-' stripped off. It'll be helpful to know which
        # arguments were specified with flags, so we'll add the '-' back to the keys.
        for key in list(args.keys()):
            if f'-{key}' in [arg for arg, _, _ in self._files_spec]:
                args[f'-{key}'] = args.pop(key)
        return args
