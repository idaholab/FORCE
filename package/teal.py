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
Created on Feb 8, 2024

@author: j-bryan (Jacob Bryan)

Runs the TEAL package as a standalone application.
"""
import sys
from TEAL.src.CashFlow_ExtMod import TEALmain
from ui import run_from_gui


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='RAVEN')
    parser.add_argument('-w', action='store_true', default=False, required=False,help='Run in the GUI')
    parser.add_argument('-iXML', nargs=1, help='XML CashFlow input file name', metavar='inp_file')
    parser.add_argument('-iINP', nargs=1, help='CashFlow input file name with the input variable list', metavar='inp_file')
    parser.add_argument('-o', nargs=1, help='Output file name', metavar='out_file')
    args = parser.parse_args()

    # Remove the -w argument from sys.argv so it doesn't interfere with TEAL's argument parsing
    if args.w:
        sys.argv.remove('-w')

    # If the -w argument is present or any of the other arguments are missing, run the GUI
    if args.w or not args.iXML or not args.iINP or not args.o:
        print('Running TEAL in GUI mode')
        run_from_gui(TEALmain)
    else:
        print('Running TEAL in command line mode')
        sys.exit(TEALmain())
