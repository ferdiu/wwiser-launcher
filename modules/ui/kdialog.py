
import subprocess
import re
import os

from . import common as Menu

class Dialog(Menu.Dialog):
    def __init__(self, title, width = 800, height = 600):
        self._width = width
        self._height = height
        super(Dialog, self).__init__("kdialog", title, width, height)
        self._set_geometry()

    def _set_geometry(self):
        self.width = ["--geometry", str(self._width) + "x" + str(self._height)]
        self.height = None

    def set_width(self, width):
        if width is None:
            self._width = 800
        else:
            self._width = width
        self._set_geometry()

    def set_height(self, height):
        if height is None:
            self._height = 600
        else:
            self._height = height
        self._set_geometry()

    def set_title(self, title):
        if title is None:
            self.title = None
        else:
            self.title = [ "--title", str(title) ]

    def _set_command(self, command):
        self.command = command

class Info(Dialog):
    def __init__(self, title, text):
        Dialog.__init__(self, title)
        self.body = [ "--msgbox", text ]

    def _do_show(self):
        return subprocess.check_output(self.compiled).decode("utf-8").replace("\r", "").replace("\n", "")

class List(Menu.List, Dialog):
    def __init__(self, title, list_type, columns):
        Dialog.__init__(self, title)
        Menu.List.__init__(self, title, list_type, columns)
        self.type = [ "--separate-output", "--" + str(list_type), str(title) ]
        self.column_number = 1
        self.row_number = 0
        self._hide_first_column = True
        for col in columns:
            self._add_column(col)

    def _add_column(self, name = None):
        self.column_number += 1

    def _do_add_row(self, checked, array):
        self.body.append(str(array.pop(0)))
        self.body.append(str(" - ".join(array)))
        self.body.append("on" if checked else "off")

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
        List.__init__(self, title, "radiolist", columns)

class Checklist(Menu.Checklist, List):
    def __init__(self, title, columns, split_char = "\n"):
        List.__init__(self, title, "checklist", columns)
        self._split_char = "\n"

    def _do_show(self):
        try:
            return subprocess.check_output(self.compiled).decode("utf-8").replace("\r", "")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class SelectFile(Menu.SelectFile, Dialog):
    def __init__(self, title, file_filter = None):
        Dialog.__init__(self, title, width = None, height = None)
        self.type = [ "--getopenfilename", os.path.expanduser('~') ]
        if file_filter:
            if file_filter.endswith(".json"):
                self.type.append("application/json")
            elif file_filter.endswith(".tar.gz") or file_filter.endswith(".tgz"):
                self.type.append("application/x-compressed-tar")


    def _do_show(self):
        try:
            return subprocess.check_output(self.compiled).decode("utf-8").replace("\r", "").replace("\n", "")
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class SelectDirectory(Menu.SelectDirectory, Dialog):
    def __init__(self, title):
        Dialog.__init__(self, title, width = None, height = None)
        self.type = [ "--getexistingdirectory" ]

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
        self.type = [ "--getexistingdirectory" ]
        self.error_dialog = ErrorDialog

class ErrorDialog(Menu.ErrorDialog, Dialog):
    def __init__(self, title, error_message):
        Dialog.__init__(self, title, width = None, height = None)
        self.set_width(300)
        self.type = [ "--error" ]
        self.body = [ str(error_message) ]

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
        self.type = [ "--yesno" ]
        self.body = str(question) + str(end)

        self.ok_label = []
        self.cancel_label = []
        if not (ok_label is None):
            self.ok_label = [ "--ok-label", str(ok_label) ]
        if not (cancel_label is None):
            self.cancel_label = [ "--no-label", str(cancel_label) ]

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
        self.type = [ "--progressbar" ]
        self.body = [ str(status_string) ]
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
                decoded_output = ""
                if isinstance(out, str):
                    decoded_output = out
                else:
                    decoded_output = out.decode('utf-8')

                composed = self.filter_process_output(composed, decoded_output, menu_process)

                if not self.is_still_running(): break

            self.wait_finish()
            menu_process.wait()

            if self.get_returncode() > 1:
                Menu.MenuException("The process exited with a non-zero code.")

        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)

class ProgressWait(Menu.ProgressWait, Progress):
    def __init__(self, title, status_string, process_to_monitor = None):
        Dialog.__init__(self, title, width = None, height = None)
        self.type = [ "--progress", "--auto-close", "--auto-kill", "--pulsate" ]
        self.body = [ "--text", str(status_string) ]
        self.monitored = None
        self._add_process_to_monitor(process_to_monitor)

    def _do_show(self):
        try:
            menu_process = subprocess.Popen(self.compiled, stdin=self.monitored.stdout)

            self.wait_finish()
            menu_process.wait()

            if self.get_returncode() > 1:
                raise Menu.MenuException("The process exited with a non-zero code.")

        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                raise Menu.MenuCancel
            else:
                raise Menu.MenuException(e.output)