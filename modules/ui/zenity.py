
import subprocess
import re

from . import common as Menu

class Dialog(Menu.Dialog):
    def __init__(self, title, width = 800, height = 600):
        super(Dialog, self).__init__("zenity", title, width, height)

    def set_width(self, width):
        if width is None:
            self.width = None
        else:
            self.width = [ "--width", str(width) ]

    def set_height(self, height):
        if height is None:
            self.height = None
        else:
            self.height = [ "--height", str(height) ]

    def set_title(self, title):
        if title is None:
            self.title = None
        else:
            self.title = [ "--title", str(title) ]

    def _set_command(self, command):
        self.command = command

class List(Menu.List, Dialog):
    def __init__(self, title, list_type, columns):
        Dialog.__init__(self, title)
        Menu.List.__init__(self, title, list_type, columns)
        self.type = [ "--list", "--" + str(list_type) + "list" ]
        self.head = [ "--column", "" ]
        self.column_number = 1
        self.row_number = 0
        self._hide_first_column = True
        for col in columns:
            self._add_column(col)
    
    def _add_column(self, name):
        self.head.append("--column")
        self.head.append(str(name))
        self.column_number += 1
    
    def _do_add_row(self, checked, array):
        self.body.append("TRUE" if checked else "FALSE")
        for string in array:
            self.body.append(str(string))

    def _additional_compile(self):
        if self._hide_first_column:
            self._add_to_compile_list([ "--hide-column", "2", "--print-column", "2" ])

    def _do_show(self):
        try:
            return subprocess.check_output(self.compiled).decode("utf-8").replace("\r", "").replace("\n", "")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class Radiolist(Menu.Radiolist, List):
    def __init__(self, title, columns):
        List.__init__(self, title, "radio", columns)
    
class Checklist(Menu.Checklist, List):
    def __init__(self, title, columns, split_char = "|"):
        List.__init__(self, title, "check", columns)
        self._split_char = split_char

    def _do_show(self):
        try:
            return List._do_show(self)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class SelectDirectory(Menu.SelectDirectory, Dialog):
    def __init__(self, title):
        Dialog.__init__(self, title, width = None, height = None)
        self.type = [ "--file-selection", "--directory" ]

    def _do_show(self):
        try:
            return subprocess.check_output(self.compiled).decode("utf-8").replace("\r", "").replace("\n", "")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class SelectWritableDirectory(Menu.SelectWritableDirectory, SelectDirectory):
    def __init__(self, title):
        Dialog.__init__(self, title, width = None, height = None)
        self.type = [ "--file-selection", "--directory" ]
        self.error_dialog = ErrorDialog

class ErrorDialog(Menu.ErrorDialog, Dialog):
    def __init__(self, title, error_message):
        Dialog.__init__(self, title, width = None, height = None)
        self.set_width(300)
        self.type = [ "--error" ]
        self.body = [ "--text", str(error_message) ]

    def _do_show(self):
        try:
            return subprocess.call(self.compiled)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class ConfirmDialog(Menu.ConfirmDialog, Dialog):
    def __init__(self, title, question, ok_label = None, cancel_label = None, end = "\n"):
        Dialog.__init__(self, title, 300, 300)
        self.type = [ "--question" ]
        self.head = [ "--text" ]
        self.body = str(question) + str(end)

        self.ok_label = []
        self.cancel_label = []
        if not (ok_label is None):
            self.ok_label = [ "--ok-label", str(ok_label) ]
        if not (cancel_label is None):
            self.cancel_label = [ "--cancel-label", str(cancel_label) ]

        self.confirm_action = None
        self.cancel_action = None
    
    def append_new_line(self, text = "", end = "\n"):
        self.body += str(text) + str(end)

    def _additional_compile(self):
        self._add_to_compile_list(self.ok_label)
        self._add_to_compile_list(self.cancel_label)

    # It make sense for a question to return a boolean
    def _do_show(self):
        try:
            return subprocess.call(self.compiled)
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class Progress(Menu.Progress, Dialog):
    def __init__(self, title, status_string, process_to_monitor = None):
        Dialog.__init__(self, title)
        self.type = [ "--progress", "--auto-close", "--percentage=0" ]
        self.body = [ "--text", str(status_string) ]
        self.monitored = None
        self._add_process_to_monitor(process_to_monitor)

    def filter_process_output(self, composed, decoded_output, menu_process):
        # Don't care about endings
        decoded_output = decoded_output.replace("\r", "").replace("\n", "")

        # Remove all non-numeric characters
        composed += re.sub("[^%0-9]", "", decoded_output)

        # If composed contains a number followed by "%" it is time to notify the menu_process
        if len(composed) > 0 and composed[-1] == "%":# and int(composed.replace("%", "")) > last_displayed:
            last_displayed = int(composed.replace("%", ""))
            composed = ""

            if isinstance(menu_process, subprocess.Popen) and not (menu_process.stdin is None):
                menu_process.stdin.write(bytes(str(last_displayed) + "\r\n", 'utf-8'))
                menu_process.stdin.flush()

        return composed

    def _do_show(self):
        try:
            menu_process = subprocess.Popen(self.compiled, stdin=subprocess.PIPE)

            composed = ""
            for out in self.get_output():
                decoded_output = out.decode('utf-8')

                composed = self.filter_process_output(composed, decoded_output, menu_process)            

                if not self.is_still_running(): break

            self.wait_finish()
            menu_process.wait()
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)
