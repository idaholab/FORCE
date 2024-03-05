from typing import Optional
import os

from tkinter import filedialog


class FileDialogController:
    def __init__(self, view, file_type=None, is_output=False, persistence=None):
        """
        Constructor
        @In, view, tk.Frame, the view
        @In, file_type, str, optional, the file type
        @In, is_output, bool, optional, whether the file is an output file
        @In, persistence, FileLocationPersistence, optional, the file location persistence
        @Out, None
        """
        self.view = view

        self.filename = None
        self.file_type = file_type
        self.persistence = persistence

        if is_output:
            if not self.file_type:
                self.file_type = 'out'
            self.view.browse_button.config(command=self.open_save_dialog)
        else:
            self.view.browse_button.config(command=self.open_selection_dialog)

    def get_filename(self):
        """
        filename getter
        @In, None
        @Out, filename, str, the filename
        """
        if not self.filename:  # None or empty string
            return None
        return self.filename

    def set_filename(self, value):
        """
        filename setter
        @In, value, str, the filename
        @Out, None
        """
        if not os.path.exists(value):
            raise FileNotFoundError(f'File {value} does not exist')
        self.filename = os.path.abspath(value)
        self.view.filename.set(os.path.basename(value))
        if self.persistence:
            self.persistence.set_location(value)

    def open_selection_dialog(self):
        """
        Open a file dialog to select an existing file
        @In, None
        @Out, None
        """
        initial_dir = self.persistence.get_location() if self.persistence else os.getcwd()
        filetypes = [(self.file_type.upper(), f'*.{self.file_type.strip().lower()}') if self.file_type else ('All Files', '*.*')]
        filename = filedialog.askopenfilename(initialdir=initial_dir, filetypes=filetypes)
        if filename:
            self.set_filename(filename)

    def open_save_dialog(self):
        """
        Open a file dialog to save a new file
        @In, None
        @Out, None
        """
        initial_dir = self.persistence.get_location() if self.persistence else os.getcwd()
        filename = filedialog.asksaveasfilename(initialdir=initial_dir, defaultextension=f'.{self.file_type}')
        if filename:
            self.set_filename(filename)
