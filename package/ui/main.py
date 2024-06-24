from typing import Callable
from ui.models import Model
from ui.controllers import Controller
from ui.views import View


def run_from_gui(func: Callable, **kwargs):
    """
    Runs the given function from the GUI.
    @In, func, Callable, the function to run
    @In, args, argparse.Namespace, optional, the parsed command-line arguments
    @In, kwargs, dict, optional, the keyword arguments for the model
    @Out, None
    """
    model = Model(func, **kwargs)
    view = View()
    controller = Controller(model, view)
    controller.start()
    # Let the controller know to clean up when the view is closed
    controller.quit(showdialog=False)
