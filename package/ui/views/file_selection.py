from typing import Optional, Callable
import tkinter as tk


class FileSelection(tk.Frame):
  """ A widget for selecting files and displaying the path after selection."""
  def __init__(self, master: tk.Widget, **kwargs):
    """
    Constructor
    @In, master, tk.Widget, the parent widget
    @In, kwargs, dict, keyword arguments
    @Out, None
    """
    super().__init__(master, **kwargs)
    self.file_selectors = {}
    self.open_in_workbench_button = None

  def new_file_selector(self, label: str):
    """
    Add a file selector to the widget
    @In, label, str, the title of the file selector
    @Out, None
    """
    frame = SelectAFile(self, label)
    frame.grid(row=len(self.file_selectors), column=0, sticky='w')
    self.file_selectors[label] = frame

  def add_open_in_workbench_button(self, command: Callable):
    """
    Create a button to open the file in Workbench. This button is only created once the first
    file selector is added to the widget. Not every application will need this button, so its
    creation is deferred until it is needed and is called by the controller.
    """
    self.open_in_workbench_button = tk.Button(self, text='Open in Workbench')
    self.open_in_workbench_button.grid(row=0, column=1, sticky='se')
    self.grid_columnconfigure(1, weight=1)
    self.open_in_workbench_button.config(command=command)


class SelectAFile(tk.Frame):
  """ A widget for selecting one file and displaying the path after selection. """
  def __init__(self,
         master: tk.Widget,
         label: Optional[str] = None):
    """
    Constructor
    @In, master, tk.Widget, the parent widget
    @In, label, Optional[str], the title of the file selector
    @Out, None
    """
    super().__init__(master)
    self.file_title = tk.Label(self, text=label)
    self.file_title.grid(row=0, column=0, columnspan=2, sticky='w')
    self.browse_button = tk.Button(self, text='Browse', width=10, padx=5)
    self.browse_button.grid(row=1, column=0, sticky='w')
    self.filename = tk.StringVar()
    self.filename.set("Select a file")  # Default filename is "Select a file", i.e. no file selected
    self.filename_label = tk.Label(self, textvariable=self.filename, bg="white", anchor='w', padx=10, pady=3)
    self.filename_label.grid(row=1, column=1, sticky='w', padx=5)
    self.grid_columnconfigure(1, weight=1)
