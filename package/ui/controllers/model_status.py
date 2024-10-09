import threading
import time
from ..models.main import ModelStatus


class ModelStatusController:
    """ Tracks if the model is running and updates the view to reflect the status. """
    def __init__(self, model, view):
        """
        Constructor
        @In, model, Model, the model
        @In, view, View, the view
        """
        self.model = model
        self.view = view
        self._model_has_run = False  # Flag to indicate the model has already been run
        self.check_model_status()

    def check_model_status(self):
        """
        Check the status of the model and update the view
        @In, None
        @Out, None
        """
        def _check_status():
            """
            Local helper function for checking the status of the model in a separate thread
            @In, None
            @Out, None
            """
            current_status = self.model.status
            while True:
                if current_status != self.model.status:
                    current_status = self.model.status
                    self.view.set_status(self.model.status)
                time.sleep(0.5)

        thread = threading.Thread(target=_check_status)
        thread.daemon = True
        thread.name = "ModelStatusChecker"
        thread.start()
