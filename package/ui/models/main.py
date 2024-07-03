import threading
from typing import Callable



class Model:
    """ Runs a function in a separate thread """
    def __init__(self, func: Callable, **kwargs):
        """
        Constructor
        @In, func, Callable, the function to run
        @In, kwargs, dict, keyword arguments to pass to the function
        @Out, None
        """
        self.func = func
        self.thread = None
        self.kwargs = kwargs

    def start(self):
        """
        Start the thread
        @In, None
        @Out, None
        """
        self.thread = threading.Thread(target=self.func, kwargs=self.kwargs)
        self.thread.daemon = True
        self.thread.start()

    def get_package_name(self):
        """
        Get the top-level package name of the model
        @In, None
        @Out, package_name, str, the package name
        """
        return self.func.__module__.split('.')[0]
