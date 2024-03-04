import sys

from .file_selection import FileSelectionController
from .text_output import TextOutputController


class Controller:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        # Initialize controllers
        self.file_selection_controller = FileSelectionController(self.model, self.view.frames["file_selection"])
        self.text_output_controller = TextOutputController(self.model, self.view.frames["text_output"])

        # Bind the run button to the model
        self.view.frames["run_abort"].run_button.config(command=self.run_model)
        # Bind the abort button to closing the window
        self.view.frames["run_abort"].abort_button.config(command=self.view.quit)

    def run_model(self):
        # Construct sys.argv from the file selectors
        sys.argv = [sys.argv[0]] + self.file_selection_controller.get_sys_args_from_file_selection()
        # Start the model
        self.model.start()
        # Update the text output
        self.view.after(10, self.text_output_controller.update_text_widget)

    def start(self):
        self.view.mainloop()
