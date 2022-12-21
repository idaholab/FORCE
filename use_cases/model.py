
import os

model_lines = open("MODELS_INDEX.md", "r").readlines()

missing = []
failed = []
finished = []
for line in model_lines[2:]:
  path = line.split("|")[2].strip()
  path = path.replace("\\_","_")
  print(path)
  if not os.path.exists(path):
    missing.append(path)
  else:
    ret = os.system("raven_framework "+path)
    if ret != 0:
      failed.append(path)
    else:
      finished.append(path)
print("missing", missing)
print("failed", failed)
