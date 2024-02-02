import tkinter as tk


class StatusPanel(tk.Frame):
    """ Provides status information on the running application. """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.status = tk.StringVar()
        self.status.set('Status: Idle')
        self.status_label = tk.Label(self, textvariable=self.status)
        self.status_label.grid(row=0, column=0, sticky='w')

        self.timer = tk.StringVar()
        self.timer.set('Time: 00:00:00')
        self.timer_label = tk.Label(self, textvariable=self.timer)
        self.timer_label.grid(row=1, column=0, sticky='w')
