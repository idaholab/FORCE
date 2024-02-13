from typing import Optional
import os
import tkinter as tk
from tkinter import filedialog


class FileSelection(tk.Frame):
    """ A widget for selecting files and displaying the path after selection."""
    def __init__(self, master: tk.Widget, **kwargs):
        """
        Constructor
        @In, master, tk.Widget, the parent widget
        @In, kwargs, dict, keyword arguments
        @Out, None
        """
        super().__init__(master, **kwargs)
        self.file_selectors = {}

    def add_file_selector(self, file_title: str, filename: Optional[str] = None):
        """
        Add a file selector to the widget
        @In, file_title, str, the title of the file selector
        @In, filename, Optional[str], the filename to set
        @Out, None
        """
        frame = SelectAFile(self, file_title)
        if filename:
            frame.set_filename(filename)
        frame.grid(row=len(self.file_selectors), column=0, sticky='w')
        self.file_selectors[file_title] = frame


class SelectAFile(tk.Frame):
    """ A widget for selecting one file and displaying the path after selection. """
    def __init__(self, master: tk.Widget, file_title: str, **kwargs):
        """
        Constructor
        @In, master, tk.Widget, the parent widget
        @In, kwargs, dict, keyword arguments
        @Out, None
        """
        super().__init__(master, **kwargs)
        self.file_title = tk.Label(self, text=file_title)
        self.file_title.grid(row=0, column=0, columnspan=2, sticky='w')
        self.button = tk.Button(self, text='Browse', command=self.select_file)
        self.button.grid(row=1, column=0, sticky='w')
        self.filename = tk.StringVar()
        self.filename.set("Select a file")  # Default filename is "Select a file", i.e. no file selected
        self.filename_label = tk.Label(self, textvariable=self.filename)
        self.filename_label.grid(row=1, column=1, sticky='w')
        self.grid_columnconfigure(1, weight=1)

    def select_file(self):
        """
        Open a file dialog to select a file
        @In, None
        @Out, None
        """
        filename = filedialog.askopenfilename()
        if filename:
            self.filename.set(os.path.relpath(filename))

    def set_filename(self, filename: str):
        """
        Set the filename
        @In, filename, str, the filename to set
        @Out, None
        """
        self.filename.set(filename)

    def get_filename(self):
        """
        Get the filename
        @In, None
        @Out, filename, str, the filename
        """
        return self.filename.get()
