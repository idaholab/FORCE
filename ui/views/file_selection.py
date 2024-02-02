import tkinter as tk
import sys


class FileSelection(tk.Frame):
    """ A widget for selecting a file and displaying the path after selection."""
    def __init__(self, master, **kwargs):
        """
        Constructor
        @In, master, tk.Widget, the parent widget
        @In, kwargs, dict, keyword arguments
        @Out, None
        """
        super().__init__(master, **kwargs)
        self.button = tk.Button(self, text='Browse')
        self.button.grid(row=0, column=0, sticky='w')

        self.filename = tk.StringVar()
        filename_from_command_line = None
        if len(sys.argv) > 1:
            filename_from_command_line = sys.argv[1]
            self.filename.set(filename_from_command_line)
        else:
            self.filename.set("Select a file")

        self.label = tk.Label(self, textvariable=self.filename)
        self.label.grid(row=0, column=1, sticky='w')
        self.grid_columnconfigure(1, weight=1)
