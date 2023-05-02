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

# This script is imported from: /raven/scripts/conversionScripts/convert_utils.py. It can be also imported from RAVEN

from __future__ import print_function, unicode_literals
import xml.dom.minidom as pxml
import xml.etree.ElementTree as ET
import os
import sys
import shutil

def createBackup(filename):
  """
    Creates a backup file based on the file at filename.  If it exists, prints an error message and returns.
    @ In, filename, string (to be appended with '.bak')
    @Out, bool, False on success or True on fail
  """
  bakname = filename+'.bak'
  if not os.path.isfile(bakname):
    shutil.copyfile(filename, bakname)
    return False
  else:
    print('ERROR! Backup file already exists:', bakname)
    print('    If you wish to continue, remove the backup and rerun the script.')
    return True


def prettify(tree):
  """
    Script for turning XML tree into something mostly RAVEN-preferred.  Does not align attributes as some devs like (yet).
    The output can be written directly to a file, as open('whatever.who','w').writelines(prettify(mytree))
    @ In, tree, xml.etree.ElementTree object, the tree form of an input file
    @Out, towrite, string, the entire contents of the desired file to write, including newlines
  """
  #make the first pass at pretty.  This will insert way too many newlines, because of how we maintain XML format.
  pretty = pxml.parseString(ET.tostring(tree.getroot())).toprettyxml(indent='  ')
  #loop over each "line" and toss empty ones, but for ending main nodes, insert a newline after.
  towrite=''
  for line in pretty.split('\n'):
    if line.strip()=='':continue
    towrite += line.rstrip()+'\n'
    if line.startswith('  </'): towrite+='\n\n'
    if line.startswith('    </'): towrite+='\n'
  return towrite
