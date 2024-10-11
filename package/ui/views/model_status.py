import tkinter as tk
from ..models.main import ModelStatus as ModelStatusEnum


class ModelStatus(tk.Frame):
  """ A widget for displaying the status of the model. """
  def __init__(self, master: tk.Widget, **kwargs):
    """
    Constructor
    @In, master, tk.Widget, the parent widget
    @In, kwargs, dict, keyword arguments
    @Out, None
    """
    super().__init__(master, **kwargs)
    self.status = tk.StringVar()
    self.status.set("Model not yet run")
    self.status_label = tk.Label(self, textvariable=self.status, bg="white", anchor='w', padx=10, pady=3)
    self.status_label.pack(side='left')
    self.grid_columnconfigure(0, weight=1)

  def set_status(self, new_status: ModelStatusEnum):
    """
    Set the status label
    @In, new_status, ModelStatusEnum, the new status
    @Out, None
    """
    self.status.set(new_status.value)
    # Change the color of the label based on the status
    if new_status == ModelStatusEnum.FINISHED:
      self.status_label.config(fg='green')
    elif new_status == ModelStatusEnum.ERROR:
      self.status_label.config(fg='red')
    else:
      self.status_label.config(fg='black')
