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
import os

if __name__ == '__main__':
    script_path = os.path.dirname(sys.argv[0])
    local_path = os.path.join(script_path,"local","bin")
    if os.path.exists(local_path):
        os.environ['PATH'] += (os.pathsep+os.path.dirname(local_path))
    print("PATH",os.environ['PATH'], "local_path", local_path)
    from HERON.src.main import main
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main())
