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
        button_width = 10
        self.abort_button = tk.Button(self, text='Abort', width=button_width)
        self.abort_button.grid(row=0, column=0, sticky='w', padx=5)

        self.run_button = tk.Button(self, text='Run', width=button_width)
        self.run_button.grid(row=0, column=1, sticky='w', padx=5)

        self.grid_columnconfigure(0, minsize=50)
        self.grid_columnconfigure(1, weight=1, minsize=50)
