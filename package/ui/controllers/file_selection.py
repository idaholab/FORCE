import os
import sys
import tkinter as tk


class FileSelectionController:
    def __init__(self, model, view):
        self.filename = view.filename
        self.file_selection = view
        self.file_selection.button.config(command=self.select_file)

    def select_file(self):
        """
        Open a file dialog to select a file
        @In, None
        @Out, None
        """
        from tkinter import filedialog
        filename = filedialog.askopenfilename()
        if filename:
            self.filename.set(os.path.relpath(filename))
            sys.argv = [sys.argv[0], filename]
