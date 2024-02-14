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

    def add_file_selector(self,
                          file_title: str,
                          filename: Optional[str] = None,
                          file_type: Optional[str] = None,
                          is_output: bool = False):
        """
        Add a file selector to the widget
        @In, file_title, str, the title of the file selector
        @In, filename, Optional[str], the filename to set
        @Out, None
        """
        if is_output:
            frame = CreateAnOutputFile(self)
        else:
            frame = SelectAFile(self, file_title, file_type)

        if filename:
            frame.set_filename(filename)
        frame.grid(row=len(self.file_selectors), column=0, sticky='w')
        self.file_selectors[file_title] = frame


class SelectAFile(tk.Frame):
    """ A widget for selecting one file and displaying the path after selection. """
    def __init__(self, master: tk.Widget, file_title: str, file_type: Optional[str] = None, **kwargs):
        """
        Constructor
        @In, master, tk.Widget, the parent widget
        @In, kwargs, dict, keyword arguments
        @Out, None
        """
        super().__init__(master, **kwargs)
        self.file_type = (file_type.upper(), f'*.{file_type.strip().lower()}') if file_type else ('All Files', '*.*')
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
        filename = filedialog.askopenfilename(initialdir=os.getcwd(), filetypes=[self.file_type])
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


class CreateAnOutputFile(tk.Frame):
    """ A widget for creating an output file. """
    def __init__(self, master: tk.Widget, **kwargs):
        """
        Constructor
        @In, master, tk.Widget, the parent widget
        @In, kwargs, dict, keyword arguments
        @Out, None
        """
        super().__init__(master, **kwargs)
        self.file_title = tk.Label(self, text="Output File")
        self.file_title.grid(row=0, column=0, columnspan=2, sticky='w')
        self.button = tk.Button(self, text='Browse', command=self.create_file)
        self.button.grid(row=1, column=0, sticky='w')
        self.filename = tk.StringVar()
        self.filename.set("Select a file")
        self.filename_label = tk.Label(self, textvariable=self.filename)
        self.filename_label.grid(row=1, column=1, sticky='w')
        self.grid_columnconfigure(1, weight=1)

    def create_file(self):
        filename = filedialog.asksaveasfilename(initialdir=os.getcwd())
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
