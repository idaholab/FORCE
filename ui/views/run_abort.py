import tkinter as tk


class RunAbort(tk.Frame):
    """ Buttons for starting and stopping the application. """
    def __init__(self, master, **kwargs):
        """
        Constructor
        @In, master, tk.Widget, the parent widget
        @In, kwargs, dict, keyword arguments
        @Out, None
        """
        super().__init__(master, **kwargs)
        self.abort_button = tk.Button(self, text='Abort')
        self.abort_button.grid(row=0, column=0, sticky='w')

        self.run_button = tk.Button(self, text='Run')
        self.run_button.grid(row=0, column=1, sticky='w')

        self.grid_columnconfigure(1, weight=1)
