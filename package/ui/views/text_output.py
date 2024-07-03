import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class TextOutput(tk.Frame):
    """ A widget for displaying text output. """
    def __init__(self, master, **kwargs):
        """
        Constructor
        @In, master, tk.Widget, the parent widget
        @In, kwargs, dict, keyword arguments
        @Out, None
        """
        super().__init__(master, **kwargs)
        self.show_hide_button = tk.Button(self, text='Hide Ouptut', pady=5, width=15)
        self.show_hide_button.grid(row=0, column=0, sticky='w')
        self.text = ScrolledText(self, state=tk.DISABLED)
        self.is_showing = True  # To use with show/hide button
        self.text.grid(row=1, column=0, sticky='nsew')
        self.grid_rowconfigure(0, minsize=50)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
