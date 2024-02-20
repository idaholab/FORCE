import os
from collections.abc import MutableMapping


class RCFile(dict):
    """ Class for handling reading and writing to a dotfile for remembering config data between runs. """
    def __init__(self, path: str):
        """
        Constructor
        @In, path, str, the path to the dotfile
        @Out, None
        """
        super().__init__()
        self.path = path
        with open(self.path, 'r') as f:
            for line in f.readlines():
                key, value = line.strip().split('=')
                self |= {key: value}

    def __del__(self):
        """
        Destructor
        @In, None
        @Out, None
        """
        # Write the entries to the file when the object is deleted
        with open(self.path, 'w') as f:
            for key, value in self.items():
                f.write(f"{key}={value}\n")
        super().__del__()


class FileLocationPersistence:
    """ A class for remembering where the case file that was last selected is located. """
    def __init__(self):
        """
        Constructor
        @In, None
        @Out, None
        """
        # A file with the location of the last selected case file
        self.rcfile = RCFile(os.path.join(os.path.dirname(__file__), '..', '.forceuirc'))

    def get_location(self):
        """
        Getter for the last file location
        @In, None
        @Out, last_location, str, the last file location
        """
        return self.rcfile.get('DEFAULT_DIR', os.path.expanduser('~'))

    def set_location(self, value):
        """
        Setter for the last file location
        @In, value, str, the last file location (file path or directory)
        @Out, None
        """
        self.rcfile['DEFAULT_DIR'] = os.path.dirname(value)
