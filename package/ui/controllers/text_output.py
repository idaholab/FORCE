import sys
import tkinter as tk


class TextOutputController:
    def __init__(self, model, view):
        """
        Constructor
        @In, model, Model, the model to control
        @In, view, TextOutput, the view to control
        """
        self.view = view
        # Redirect stdout and stderr to the Text widget
        sys.stdout = Redirect(self.view.text)
        sys.stderr = Redirect(self.view.text)
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
