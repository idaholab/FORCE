from typing import Callable
from models import Model
from controllers import Controller
from views import View


def run_from_gui(func: Callable):
    model = Model(func)
    view = View()
    controller = Controller(model, view)
    controller.start()


if __name__ == "__main__":
    # from HERON.src.main import main
    from ravenframework.Driver import main
    import sys
    run_from_gui(lambda: sys.exit(main(False)))
