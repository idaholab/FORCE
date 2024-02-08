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
import argparse
from utils import add_local_bin_to_path


if __name__ == '__main__':
    add_local_bin_to_path()
    from HERON.src.main import main
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    parser = argparse.ArgumentParser(description='HERON')
    parser.add_argument('-w', action='store_true', default=False, required=False, help='Run in the GUI')
    parser.add_argument('file', nargs='?', help='Case file to run')
    args = parser.parse_args()
    if args.file:
        sys.argv = [sys.argv[0], args.file]
    if args.w or not args.file:  # if asked to or if no file is passed, run the GUI
        run_from_gui(main)
    else:
        main()
