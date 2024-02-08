from typing import Callable
from ui.models import Model
from ui.controllers import Controller
from ui.views import View


def run_from_gui(func: Callable):
    model = Model(func)
    view = View()
    controller = Controller(model, view)
    controller.start()
