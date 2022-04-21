
import os
import sys
import xml.etree.ElementTree as ET


def modify_baseline(root):
  """ root should be outer.xml """
  # change runinfo
  runinfo = root.find('RunInfo')
  runinfo.find('JobName').text = 'B' + runinfo.find('JobName').text
  runinfo.find('WorkingDir').text = 'Baseline'
  runinfo.find('batchSize').text = '1'
  runinfo.find('Sequence').text = 'baseline'
  # steps
  mr = root.find('Steps').find('MultiRun')
  mr.attrib['name'] = 'baseline'
  opt = mr.find('Optimizer')
  opt.tag = 'Sampler'
  opt.attrib['class'] = 'Samplers'
  opt.attrib['type'] = 'MonteCarlo'
  opt.text = 'mc'
  mr.remove(mr.find('SolutionExport'))
  for out in mr.findall('Output'):
    out.text = 'baseline'
  # data objects
  for dobj in root.find('DataObjects'):
    if dobj.attrib['name'] == 'opt_eval':
      dobj.attrib['name'] = 'baseline'
      dobj.find('Output').text = 'mean_NPV,std_NPV'
    else:
      root.find('DataObjects').remove(dobj)
  # optimizer -> sampler
  opters = root.find('Optimizers')
  opters.tag = 'Samplers'
  opter = opters.find('GradientDescent')
  opter.tag = 'MonteCarlo'
  opter.attrib['name'] = 'mc'
  opter.remove(opter.find('objective'))
  opter.remove(opter.find('TargetEvaluation'))
  opter.remove(opter.find('Constraint'))
  init = opter.find('samplerInit')
  init.remove(init.find('writeSteps'))
  init.remove(init.find('type'))
  init.find('limit').text = '1'
  opter.remove(opter.find('gradient'))
  opter.remove(opter.find('stepSize'))
  opter.remove(opter.find('acceptance'))
  opter.remove(opter.find('convergence'))
  for varnode in opter.findall('variable'):
    varnode.tag = 'constant'
    varnode.text = '0'
    varnode.remove(varnode.find('distribution'))
    varnode.remove(varnode.find('initial'))
  # outstream
  pr = root.find('OutStreams').find('Print')
  pr.attrib['name'] = 'baseline'
  pr.find('source').text = 'baseline'
  pr.remove(pr.find('clusterLabel'))
  # functions
  ## not for now, just in case it's needed for copying




if __name__ == '__main__':
  if len(sys.argv) < 2:
    raise IOError('Specify the target "outer.xml" to create a baseline case for!')
  cwd = os.getcwd()
  target = sys.argv[1]
  target = os.path.abspath(os.path.join(cwd, target))
  outer = ET.parse(target).getroot()
  modify_baseline(outer)
  outfile = os.path.join(os.path.dirname(target), 'baseline.xml')
  with open(outfile, 'w') as f:
    f.write(ET.tostring(outer, encoding='unicode'))
  print(f'wrote baseline.xml to {outfile}')