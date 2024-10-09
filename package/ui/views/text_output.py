import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from .model_status import ModelStatus


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
        self.model_status = ModelStatus(self)
        self.model_status.grid(row=0, column=1, sticky='e')
        self.text = ScrolledText(self, state=tk.DISABLED)
        self.is_showing = True  # To use with show/hide button
        self.text.grid(row=1, column=0, sticky='nsew', columnspan=2)
        self.grid_rowconfigure(0, minsize=50)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def show_text_output(self):
        """
        Show the text output widget
        @In, None
        @Out, None
        """
        self.text.grid(row=1, column=0, sticky='nsew', columnspan=2)
        self.show_hide_button.config(text='Hide Output')
        self.is_showing = True
        # Set window to default size
        self.master.update()
        self.master.geometry("800x600")

    def hide_text_output(self):
        """
        Hide the text output widget
        @In, None
        @Out, None
        """
        self.text.grid_forget()
        self.show_hide_button.config(text='Show Output')
        self.is_showing = False
        # Reduce window size
        self.master.update()
        self.master.geometry("350x175")
