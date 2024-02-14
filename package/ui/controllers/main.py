import sys

from .file_selection import FileSelectionController
from .status import StatusController
from .text_output import TextOutputController


class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # Initialize controllers
        self.file_selection_controller = FileSelectionController(self.model, self.view.frames["file_selection"])
        self.status_panel_controller = StatusController(self.model, self.view.frames["status_panel"])
        self.text_output_controller = TextOutputController(self.model, self.view.frames["text_output"])

        # Bind the run button to the model
        self.view.frames["run_abort"].run_button.config(command=self.run_model)
        # Bind the abort button to closing the window
        self.view.frames["run_abort"].abort_button.config(command=self.view.quit)

        # Bind Ctrl-C to closing the window for convenvience
        self.view.root.bind('<Control-c>', lambda cmd: self.view.root.destroy())

    def run_model(self):
        # Construct sys.argv from the file selectors
        sys.argv = [sys.argv[0]] + self.file_selection_controller.get_files()
        print('sys.argv:', sys.argv)
        # Start the model
        self.model.start()
        # Status update loop
        self.view.frames["status_panel"].after(100, self.status_panel_controller.update_status)

    def start(self):
        self.view.mainloop()
