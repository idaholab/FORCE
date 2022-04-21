
import os
import sys
import copy
import argparse
from pathlib import Path
from itertools import product
import xml.etree.ElementTree as ET

import pandas as pd

# raven xmlUtils
parser = argparse.ArgumentParser()
parser.add_argument(
    '-r', '--raven-dir', type=Path,
    default=Path('~/projects/raven/framework')
)
args = parser.parse_args()
raven_loc = args.raven_dir.expanduser()
if not raven_loc.exists():
    raise OSError(
        f"{raven_loc} does not exist!\n"
        "Try using --raven-dir flag to specify raven framework directory."
    )
sys.path.append(str(raven_loc))
from utils import xmlUtils as xu

script_loc = (Path(__file__)/'..').resolve()
data_loc = script_loc/'..'/'data'

def train_name(case):
  _, strat, struc = case
  if strat == 'Nominal':
    a = 'default'
  elif strat == 'RPS':
    a = 'rps'
  elif strat == 'CarbonTax':
    a = 'carbontax'
  if struc == 'Default':
    b = ''
  elif struc == 'LNHR':
    b = '_lnhr'
  return f'{a}{b}'

def qsub_name(case, reg):
  _, strat, struc = case
  if strat == 'Nominal':
    a = 'Nom'
  elif strat == 'RPS':
    a = 'RPS'
  elif strat == 'CarbonTax':
    a = 'CT'
  if struc == 'Default':
    b = 'Def'
  elif struc == 'LNHR':
    b = 'LNHR'
  return f'{reg[0]}_{a}_{b}'

def fill_reg(case):
  state, strat, struc = case
  root = ET.parse(script_loc/'reg_template.xml').getroot()
  # case name
  root.find('Case').attrib['name'] = f'R_{strat}_{struc}'
  # update labels
  labels = root.find('Case').findall('label')
  for l in labels:
    if l.attrib['name'] == 'state':
      l.text = state
    elif l.attrib['name'] == 'strategy':
      l.text = strat
    elif l.attrib['name'] == 'price_struct':
      l.text = struc
  # update ARMA location
  arma = root.find('DataGenerators').find('ARMA')
  arma.text = arma.text.replace('CASE', train_name(case)).replace('STATE', state)
  return root

def fill_dereg(case):
  state, strat, struc = case
  root = ET.parse(script_loc/'dereg_template.xml').getroot()
  # case name
  root.find('Case').attrib['name'] = f'D_{strat}_{struc}'
  # update labels
  labels = root.find('Case').findall('label')
  for l in labels:
    if l.attrib['name'] == 'state':
      l.text = state
    elif l.attrib['name'] == 'strategy':
      l.text = strat
    elif l.attrib['name'] == 'price_struct':
      l.text = struc
  # update ARMA location
  arma = root.find('DataGenerators').find('ARMA')
  arma.text = arma.text.replace('CASE', train_name(case)).replace('STATE', state)
  return root

def write_template(xml, case, reg):
  state, strat, struc = case
  name = '_'.join(case)
  dirname = f'{reg}/' + name
  path = script_loc/dirname
  path.mkdir(parents=True, exist_ok=True)
  full_path = (path/f'{name}.xml').resolve()
  xu.toFile(full_path, xml)
  print(f'... wrote {path.name} to {full_path}.')

def copy_qsub(case, reg):
  state, strat, struc = case
  name = '_'.join(case)
  dirname = f'{reg}/' + name
  source = script_loc/'qsub_script_template.sh'
  casename = qsub_name(case, reg)
  text = source.read_text()
  text = text.replace('CASE_TEMPLATE', casename)
  (script_loc/dirname/'qsub_script.sh').write_text(text)

if __name__ == '__main__':
  states = ['IL']
  strategies = ['Nominal', 'RPS', 'CarbonTax']
  price_structs = ['Default', 'LNHR']
  cases = product(states, strategies, price_structs)
  for case in cases:
    print('Case:', ' | '.join(case))
    print(' ... filling ...')
    xml_dereg = fill_dereg(case)
    xml_reg = fill_reg(case)
    print(' ... writing ...')
    write_template(xml_dereg, case, reg='Deregulated')
    write_template(xml_reg, case, reg='Regulated')
  print('done')
