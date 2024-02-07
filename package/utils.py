import sys
import os


def add_local_bin_to_path():
    script_path = os.path.dirname(sys.argv[0])
    local_path = os.path.join(script_path,"local","bin")
    if os.path.exists(local_path):
        os.environ['PATH'] += (os.pathsep+local_path)
        for root, dirs, files in os.walk(local_path):
            if 'bin' in dirs:
                print('Adding', os.path.join(root,'bin'),'to PATH')
                os.environ['PATH'] += (os.pathsep+os.path.join(root,'bin'))
