import threading
from typing import Callable
import time
from enum import Enum


class ModelStatus(Enum):
  """ Enum for model status """
  NOT_STARTED = "Not yet run"
  RUNNING = "Running"
  FINISHED = "Finished"
  ERROR = "Error"


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
    self.status = ModelStatus.NOT_STARTED

  def start(self):
    """
    Start the thread
    @In, None
    @Out, None
    """
    def func_wrapper():
      """
      Wrapper for the function to run and set the status to FINISHED when done
      @In, None
      @Out, None
      """
      self.status = ModelStatus.RUNNING
      try:
        self.func(**self.kwargs)
      except:
        self.status = ModelStatus.ERROR
      else:
        self.status = ModelStatus.FINISHED

    self.thread = threading.Thread(target=func_wrapper)
    self.thread.daemon = True
    self.thread.name = self.get_package_name()
    self.thread.start()

  def get_package_name(self):
    """
    Get the top-level package name of the model
    @In, None
    @Out, package_name, str, the package name
    """
    return self.func.__module__.split('.')[0]
