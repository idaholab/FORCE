
# Copyright 2020, Battelle Energy Alliance, LLC
# ALL RIGHTS RESERVED


import os
import shutil
import sys
import platform

HERON_LOC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# First attempt to find HERON/src assuming the HERON and FORCE are in the same folder
HERON_LOC1 = (HERON_LOC.split("FORCE"))[0]+"HERON/src" 
# Second attempt to find HERON/src assuming that HERON is under FORCE 
HERON_LOC2 = (HERON_LOC.split("FORCE"))[0]+"FORCE/HERON/src" 

# try:
#   from RavenFramework import RavenFramework as RavenTester
# except ModuleNotFoundError:
# get heron utilities
sys.path.append(HERON_LOC)
# import _utils as hutils
sys.path.pop()

# get RAVEN base testers
# RAVEN_LOC = hutils.get_raven_loc()
# First attempt to find raven assuming that raven and FORCE are in the same folder
RAVEN_LOC1 = (HERON_LOC.split("FORCE"))[0]+"raven" 
# Second attempt to find raven assuming that raven is under FORCE
RAVEN_LOC2 = (HERON_LOC.split("FORCE"))[0]+"FORCE/raven/src"

if os.path.exists(RAVEN_LOC1):
  RAVEN_LOC = RAVEN_LOC1
elif os.path.exists(RAVEN_LOC2): 
  RAVEN_LOC = RAVEN_LOC2
else:
  print("can't find RAVEN!")    



TESTER_LOC = os.path.join(RAVEN_LOC, '..', 'scripts', 'TestHarness', 'testers')
sys.path.append(TESTER_LOC)
RavenFramework_test_loc = RAVEN_LOC + "/scripts/TestHarness/testers"
sys.path.append(RavenFramework_test_loc)

from RavenFramework import RavenFramework as RavenTester
sys.path.pop()

class HeronIntegration(RavenTester):
  """
    Defines testing mechanics for HERON integration tests; that is, tests that
    run the full HERON-RAVEN suite on a case.
  """

  # TODO extend get_valid_params?
  @staticmethod
  def get_valid_params():
    """
      Returns the valid parameters.
      @ In, None
      @ Out, params, _ValidParameters, return the parameters.
    """
    params = RavenTester.get_valid_params()
    params.add_param('kind', 'both', 'Run "both" HERON and RAVEN or "heron_only"')
    return params

  def __init__(self, name, param):
    """
      Constructor.
      @ In, name, str, name of test
      @ In, params, dict, test parameters
      @ Out, None
    """
    RavenTester.__init__(self, name, param)
    heron_guess1 = os.path.join(HERON_LOC1, '..', 'heron')
    heron_guess2 = os.path.join(HERON_LOC2, '..', 'heron')
    if os.path.exists(heron_guess1):
      self.heron_driver = heron_guess1 
    elif os.path.exists(heron_guess2):
      self.heron_driver = heron_guess2    
    elif shutil.which("heron") is not None:
      self.heron_driver = "heron"
    else:
      print("ERROR unable to find heron.  Tried: "+heron_guess1, +heron_guess2)
    # NOTE: self.driver is RAVEN driver (e.g. /path/to/Driver.py)

  def get_command(self):
    """
      Gets the command line commands to run this test
      @ In, None
      @ Out, cmd, str, command to run
    """
    cmd = ''
    cmd, heron_inp = self.get_heron_command(cmd)
    if self.specs["kind"].lower() == "both":
      cmd += ' && '
      cmd = self.get_raven_command(cmd, heron_inp)
    elif self.specs["kind"].lower() == "heron_only":
      pass
    else:
      print("ERROR unknown HeronIntegration command kind", self.specs["kind"])
    return cmd

  def get_heron_command(self, cmd):
    """
      Generates command for running heron
      @ In, cmd, string
      @ Out, cmd, string, updated command
      @ Out, heron_inp
    """
    test_loc = os.path.abspath(self.specs['test_dir'])
    # HERON expects to be run in the dir of the input file currently, TODO fix this
    cmd += f' cd {test_loc} && '
    # clear the subdirectory if it's present
    cmd += ' rm -rf *_o/ && '
    # run HERON first
    heron_inp = os.path.join(test_loc, self.specs['input'])
    # Windows is a little different with bash scripts
    if platform.system() == 'Windows':
      cmd += ' bash.exe '
    cmd += f' {self.heron_driver} {heron_inp}'
    return cmd, heron_inp

  def get_raven_command(self, cmd, heron_inp):
    """
      Get command for running raven
      @ In, cmd, string
      @ In, heron_inp, path to heron input
      @ Out, cmd, string, updated command
    """
    python = self._get_python_command()
    raven_inp = os.path.abspath(os.path.join(os.path.dirname(heron_inp), 'outer.xml'))
    cmd += f' {python} {self.driver} {raven_inp}'
    return cmd