import tkinter as tk


class Root(tk.Tk):
    """ The main window. """
    def __init__(self, **kwargs):
        """
        Constructor
        @In, kwargs, dict, keyword arguments for tkinter.Tk
        @Out, None
        """
        super().__init__(**kwargs)
        self.title('FORCE')
        self.geometry('800x600')
        self.grid()
        self.bind('<Control-c>', self.quit)
