import sys
import os


def add_local_bin_to_path():
    """
    Adds the local/bin directory to the system path in order to find ipopt and other executables
    """
    script_path = os.path.dirname(sys.argv[0])
    local_path = os.path.join(script_path,"local","bin")
    # Add script path (to get raven_framework in the path, and local/bin
    #  to get things like ipopt in the path.
    os.environ['PATH'] += (os.pathsep+local_path+os.pathsep+script_path)
    # Recursively add all additional "bin" directories in "local/bin" to the system path
    if os.path.exists(local_path):
        os.environ['PATH'] += (os.pathsep+local_path)
        for root, dirs, files in os.walk(local_path):
            if 'bin' in dirs:
                os.environ['PATH'] += (os.pathsep+os.path.join(root,'bin'))
