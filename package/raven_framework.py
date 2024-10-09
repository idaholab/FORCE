#!/usr/bin/env python
# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on Feb 14, 2022

@author: cogljj

This is a package that properly imports Driver and runs it.
"""
import sys
from ravenframework.Driver import main
from ui import run_from_gui
from utils import add_local_bin_to_path
import multiprocessing


if __name__ == '__main__':
    # For Windows, this is required to avoid an infinite loop when running a multiprocessing script from a frozen executable.
    # cx_Freeze provides a hook for this that is supposed to be called automatically to fix this issue on all platforms,
    # but for now, it doesn't seem to resolve the issue on macOS.
    multiprocessing.freeze_support()

    # Adds the "local/bin" directory to the system path in order to find ipopt and other executables
    add_local_bin_to_path()

    # Parse the command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='RAVEN')
    parser.add_argument('-w', action='store_true', default=False, required=False,help='Run in the GUI')
    parser.add_argument('input', nargs='*', help='RAVEN input file')
    args, unknown = parser.parse_known_args()

    # More than one argument may be parsed for "input". Move any arguments that aren't an XML file to
    # the unknown arguments list.
    args_to_move = []
    for arg in args.input:
       if not arg.endswith('.xml'):
          args_to_move.append(arg)
    for arg in args_to_move:
       args.input.remove(arg)
       unknown.insert(0, arg)

    # sys.argv is used by the main function, so we need to remove the -w argument
    if args.w:
        sys.argv.remove('-w')

    if args.w or not args.input:  # run the GUI if asked to (-w) or if no input file is given
        run_from_gui(main, checkLibraries=True)
    else:
        sys.exit(main(True))
