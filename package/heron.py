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
import re
import sys
from HERON.src.main import main
from ui import run_from_gui
from ui.utils import run_in_workbench
from utils import add_local_bin_to_path


if __name__ == '__main__':
    # Adds the "local/bin" directory to the system path in order to find ipopt and other executables
    add_local_bin_to_path()

    # Parse the command line arguments
    import argparse
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    parser = argparse.ArgumentParser(description='HERON')
    parser.add_argument('-w', action='store_true', default=False, required=False, help='Run in the GUI')
    parser.add_argument('--definition', action="store_true", dest="definition", help='HERON input file definition compatible with the NEAMS Workbench')
    parser.add_argument('input', nargs='?', help='HERON input file')
    args, unknown = parser.parse_known_args()

    # if the input file is not an xml file, assume it's an unknown argument
    if args.input and not args.input.endswith('.xml'):
        unknown.insert(0, args.input)
        args.input = None
    # remove the -w argument from sys.argv so it doesn't interfere with HERON's argument parsing
    if args.w:
        sys.argv.remove('-w')

    if (args.w or not args.input) and not args.definition:  # if asked to or if no file is passed, run the GUI
        # try:
        #     run_in_workbench(args.input)
        # except RuntimeError:
        #     run_from_gui(main)
        run_from_gui(main)
    else:
        main()
