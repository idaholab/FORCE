from .root import Root
from .file_selection import FileSelection
from .status import StatusPanel
from .text_output import TextOutput
from .run_abort import RunAbort

from tkinter.messagebox import askokcancel


class View:
    """ Main view class. """
    def __init__(self):
        """
        Main view constructor. Sets up main window by adding essential frames.
        @In, None
        @Out, None
        """
        self.root = Root()
        self.frames = {}

        # add frames to the view in a grid layout
        self.add_frame('file_selection', FileSelection(self.root),
                       row=0, column=0, sticky='nsew', padx=10, pady=5)
        self.add_frame('status_panel', StatusPanel(self.root),
                       row=1, column=0, sticky='nsew', padx=10, pady=5)
        self.add_frame('text_output', TextOutput(self.root),
                       row=2, column=0, sticky='nsew', padx=10, pady=10)
        self.add_frame('run_abort', RunAbort(self.root),
                       row=3, column=0, sticky='se', padx=10, pady=5)

        # Let the text output frame expand to fill the available space
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def add_frame(self, name, frame, **kwargs):
        """
        Add a frame to the view
        @In, name, str, the name of the frame
        @In, frame, tk.Frame, the frame to add
        @In, kwargs, dict, keyword arguments for grid
        @Out, None
        """
        self.frames[name] = frame
        frame.grid(**kwargs)

    def mainloop(self):
        """
        Run the application main loop
        @In, None
        @Out, None
        """
        self.root.mainloop()

    def quit(self):
        """
        Quit the application
        @In, None
        @Out, None
        """
        response = askokcancel('Abort run', 'Are you sure you want to abort? '
                               'This will close the window and any text output will be lost.')
        if response:
            self.root.quit()
