import tkinter as tk
import datetime


class StatusController(tk.Frame):
    """ Controller for the status panel. """
    def __init__(self, model, view):
        self.model = model
        self.view = view

    def set_status(self, status):
        self.view.status.set(f'Status: {status}')

    def set_timer(self, time):
        self.view.timer.set(f'Time: {time}')

    def update_status(self):
        self.set_status('Running' if self.model.is_alive() else 'Idle')
        time_elapsed = round(self.model.get_execution_time())
        self.set_timer(f'{datetime.timedelta(seconds=time_elapsed)}')
        self.view.update()
        self.view.after(100, self.update_status)
