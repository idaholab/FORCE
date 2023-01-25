
import os
import sys
import subprocess

model_lines = open("MODELS_INDEX.md", "r").readlines()

missing = []
failed = []
finished = []
full_output = open("model_run_out.txt", "w")
for line in model_lines[2:]:
  path = line.split("|")[2].strip()
  path = path.replace("\\_","_")
  print(path)
  if not os.path.exists(path):
    missing.append(path)
  else:
    print("Running "+path)
    print("Running",path,file=full_output)
    ret = subprocess.run(["raven_framework",path], capture_output=True, text=True)
    print("returncode",ret.returncode)
    print("returncode",ret.returncode,file=full_output)
    print(ret.stdout, file=full_output)
    print(ret.stderr, file=full_output)
    if ret.returncode != 0:
      print(ret.stdout)
      print(ret.stderr)
      failed.append(path)
    else:
      finished.append(path)
print("missing", missing)
print("failed", failed)
print("finished", finished)
sys.exit(len(missing) + len(failed))
