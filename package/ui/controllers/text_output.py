import sys
import io
import threading
import tkinter as tk
import time


class TextOutputController:
    def __init__(self, model, view):
        """
        Constructor
        @In, model, Model, the model to control
        @In, view, TextOutput, the view to control
        """
        self.view = view
        self.redirector = StdoutRedirector(self.view.text)
        self.redirector.start()
        # Define show/hide button behavior
        self.view.show_hide_button.config(command=self.toggle_show_text)

    def toggle_show_text(self):
        """
        Toggle the visibility of the output text widget
        @In, None
        @Out, None
        """
        if self.view.is_showing:  # Hide output
            self.view.text.grid_forget()
            self.view.show_hide_button.config(text='Show Output')
        else:  # Show output
            self.view.text.grid(row=1, column=0, sticky='nsew')
            self.view.show_hide_button.config(text='Hide Output')
        self.view.is_showing = not self.view.is_showing


class StdoutRedirector:
    """ Redirects stdout to a tkinter widget """
    def __init__(self, widget: tk.Widget):
        """
        Constructor
        @In, widget, tk.Widget, the widget to redirect stdout to
        @Out, None
        """
        self.widget = widget
        self.redirect_output = io.StringIO()
        sys.stdout = self.redirect_output
        sys.stderr = self.redirect_output

    def start(self):
        """
        Start the redirector. Uses a daemon thread to monitor the output.
        @In, None
        @Out, None
        """
        self.monitor_thread = threading.Thread(target=self.monitor_output)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def monitor_output(self):
        """
        Monitors the output and updates the widget
        @In, None
        @Out, None
        """
        while True:
            # Get the buffer's contents, then clear it
            text = self.redirect_output.getvalue()
            self.redirect_output.seek(0)
            self.redirect_output.truncate(0)

            # Update the widget's text
            if text:
                self.widget.config(state=tk.NORMAL)
                self.widget.insert(tk.END, text)
                self.widget.config(state=tk.DISABLED)
                self.widget.see(tk.END)

            # Sleep to prevent busy-waiting
            time.sleep(0.1)  # FIXME: expose this as a parameter
