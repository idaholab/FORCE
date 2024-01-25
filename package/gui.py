"""
Implements a GUI for running the HERON and RAVEN main scripts using tkinter.
"""

import sys
import os
import threading
import time
import datetime
from collections.abc import Callable

import tkinter as tk
from tkinter import filedialog
from tkinter.messagebox import askokcancel
from tkinter.scrolledtext import ScrolledText


class Redirect:
    """ Redirect stdout to tkinter widget """
    def __init__(self, widget: tk.Widget, autoscroll: bool = True) -> None:
        """
        Constructor
        @In, widget, tk.Widget, the widget to redirect output to
        @In, autoscroll, bool, if True, scroll to end of output (default True)
        @Out, None
        """
        self.widget = widget
        self.autoscroll = autoscroll

    def write(self, text: str) -> None:
        """
        Write text to widget
        @In, text, str, the text to write
        @Out, None
        """
        self.widget.configure(state=tk.NORMAL)
        self.widget.insert(tk.END, text)
        self.widget.configure(state=tk.DISABLED)
        if self.autoscroll:
            self.widget.see(tk.END)  # autoscroll
        self.widget.update()

    def flush(self) -> None:
        """
        Flush the widget
        @In, None
        @Out, None
        """
        # flush method is required here for when stdout is reset to sys.__stdout__,
        # but we don't need to do anything
        pass


class BasicGUI:
    """ A basic graphical user interface for running FORCE tools. """
    def __init__(self) -> None:
        """
        Constructor. Builds the GUI.
        @In, None
        @Out, None
        """
        # Default window size for different states
        self._window_size_no_output   = '300x100'
        self._window_size_with_output = '550x400'

        # Root window
        self._root = tk.Tk()
        self._root.title('FORCE')
        self._root.geometry(self._window_size_no_output)
        self._root.resizable(width=True, height=True)

        # The window is divided into three frames:
        #   1. File selection
        #   2. Status panel
        #   2. Output text
        #   3. "Show/Hide Output", "Run" and "Abort" buttons
        file_frame = tk.Frame(self._root, height=20)
        file_frame.grid(column=0, row=0, sticky=tk.NW)
        status_frame = tk.Frame(self._root, height=40)
        status_frame.grid(column=0, row=1, sticky=tk.NW)
        output_frame = tk.Frame(self._root)
        output_frame.grid(column=0, row=2, sticky=tk.NW)
        buttons_frame = tk.Frame(self._root, height=20)
        buttons_frame.grid(column=0, row=3, sticky=tk.NSEW)
        self._root.grid_columnconfigure(0, weight=1)
        self._root.grid_rowconfigure(2, weight=1)

        # File selection
        self._xml_file_to_run = ""
        self._file_button = tk.Button(file_frame, text='Select File', command=self.get_file_to_run)
        self._file_button.grid(column=0, row=0, sticky=tk.W)
        file_label = tk.Label(file_frame, text='File:')
        file_label.grid(column=1, row=0, sticky=tk.W)
        self._file_to_run_label = tk.Label(file_frame, text=self._xml_file_to_run)
        self._file_to_run_label.grid(column=2, row=0, sticky=tk.W)

        # Status panel
        self._status_label = tk.Label(status_frame, text='Status: No file selected.')
        self._status_label.grid(column=0, row=0, sticky=tk.W)
        self._time_elapsed_label = tk.Label(status_frame, text='Time elapsed:')
        self._time_elapsed_label.grid(column=0, row=1, sticky=tk.W)

        # Script output
        # Text widget for showing script output, hidden by default
        self._text = ScrolledText(output_frame, wrap='char')
        self._text.configure(state=tk.DISABLED)
        self._text.pack_forget()

        # Buttons for showing and hiding the text widget, running the script, and canceling the run
        self._show_output = tk.Button(buttons_frame, text='Show Output', command=self._show_text)
        self._show_output.grid(column=0, row=0, sticky=tk.SW)
        self._abort_button = tk.Button(buttons_frame, text='Abort', command=self._ask_abort, state=tk.DISABLED)
        self._abort_button.grid(column=1, row=0, sticky=tk.SE)
        self._run_button = tk.Button(buttons_frame, text='Run', state=tk.DISABLED)
        self._run_button.grid(column=2, row=0, sticky=tk.SE)
        buttons_frame.grid_rowconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)

        # Bind Ctrl+C to the "Abort" button for convenience
        self._root.bind('<Control-c>', lambda event: self._abort_button.invoke())

        # Keep track of thread start time to calculate time elapsed
        self._thread_start_time = 0.0

    def _show_text(self) -> None:
        """
        Show the text widget and scrollbar.
        @In, None
        @Out, None
        """
        self._show_output.configure(text='Hide Output', command=self._hide_text)
        self._text.pack(fill=tk.BOTH, expand=tk.YES)
        self._root.geometry(self._window_size_with_output)

    def _hide_text(self) -> None:
        """
        Hide the text widget and scrollbar.
        @In, None
        @Out, None
        """
        self._show_output.configure(text='Show Output', command=self._show_text)
        self._text.pack_forget()
        self._root.geometry(self._window_size_no_output)

    def _ask_abort(self) -> None:
        """
        Abort the run.
        @In, None
        @Out, None
        """
        response = askokcancel('Abort run', 'Are you sure you want to abort? '
                               'This will close the window and any text output will be lost.')
        if response:
            # TODO: We could dump the text output to a file here for better debugging
            self._root.destroy()

    def get_file_to_run(self) -> str:
        """
        Get a file to run using a file dialog.
        @In, None
        @Out, None
        """
        filename = filedialog.askopenfilename(title='Select File to Run', filetypes=[('XML files', '*.xml')])
        self._xml_file_to_run = filename
        if filename:  # activate the run button if a file was selected
            self._file_to_run_label.configure(text=os.path.relpath(self._xml_file_to_run))
            self._run_button.configure(state=tk.NORMAL)
            self._update_status(status='Ready')

    def _update_status(self, status: str | None = None, time_elapsed: float | None = None) -> None:
        """
        Update the status panel.
        @In, status, str, the status to display
        @In, time_elapsed, str, the time elapsed to display
        @Out, None
        """
        if status is not None:
            self._status_label.configure(text='Status: ' + status)
        if time_elapsed is not None:
            time_elapsed = datetime.timedelta(seconds=round(time_elapsed))
            self._time_elapsed_label.configure(text='Time elapsed: ' + str(time_elapsed))

    def _check_thread(self, thread: threading.Thread) -> None:
        """
        Check if a thread is still running.
        @In, thread, threading.Thread, the thread to check
        @Out, None
        """
        time_elapsed = time.time() - self._thread_start_time
        if thread.is_alive():
            self._root.after(100, self._check_thread, thread)
            self._update_status(time_elapsed=time_elapsed)
        else:
            self._run_button.configure(state=tk.NORMAL)
            self._abort_button.configure(state=tk.DISABLED)
            self._update_status(status='Done', time_elapsed=time_elapsed)

    def run_function(self, func: Callable) -> None:
        """
        Run a function in the GUI.
        @In, func, Callable, the function to run
        @Out, None
        """
        # NOTE: Threading is used here instead of multiprocessing because the multiprocessing
        # module does not work well with the combination of frozen executables (such as those
        # produced with cx_Freeze) and tkinter. Multiprocessing implements a number of different
        # start methods which are used to start new processes. The 'spawn' and 'forkserver'
        # methods cannot be used with frozen executables, and the 'fork' method requires that
        # the main script not use threads, making it unsuitable for use with tkinter. See
        # https://docs.python.org/3/library/multiprocessing.html#the-process-class. The downside
        # to using threading is that the threading API does not support terminating a thread
        # from the outside. We stop a running thread by having it set in daemon mode, closing
        # the GUI window, and ending the main thread. This will kill the daemon thread.

        def make_thread_and_run() -> None:
            """
            Make a thread to run the function and run the thread.
            @In, None
            @Out, None
            """
            # Configure GUI state to show that the function is running
            self._run_button.configure(state=tk.DISABLED)
            self._abort_button.configure(state=tk.NORMAL)
            self._update_status(status='Running')
            self._thread_start_time = time.time()
            # Add XML file that was selected to sys.argv to be passed to the function
            sys.argv.append(self._xml_file_to_run)
            # Run the function in a thread
            thread = threading.Thread(target=func)
            thread.daemon = True  # makes sure the thread is killed when the GUI is closed
            thread.start()
            # Check if the thread is still running
            self._root.after(100, self._check_thread, thread)

        # Set the run button command to run the function
        self._run_button.configure(command=make_thread_and_run)

        # Run the GUI, redirecting stdout to the text widget
        sys.stdout = Redirect(self._text)
        self._root.mainloop()


def test_run() -> None:
    """
    Test function to run when the "Run" button is pressed.
    @In, None
    @Out, None
    """
    print('Running test function.')
    for i in range(10):
        print(i)
        time.sleep(0.2)
    print('Done.')


# Some test code
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    gui = BasicGUI()
    gui.run_function(test_run)
