
import subprocess
import os

from abc import ABC, abstractmethod

class MenuException(Exception): pass
class MenuCancel(Exception): pass
class NoAdditionalCompile(Exception): pass

def raise_cancel():
    raise MenuCancel("Canceled by the user.")

def raise_ex(ex):
    raise MenuException(ex)

class Dialog(ABC):
    def __init__(self, command, title, width = None, height = None):
        self.command = command
        self._set_command(command)
        self.set_title(title)
        self.set_width(width)
        self.set_height(height)
        self.type = []
        self.head = []
        self.body = []

    def _add_to_compile_list(self, command_portion):
        if command_portion is None:
            pass
        elif isinstance(command_portion, list):
            for portion in command_portion:
                self.compiled.append(portion)
        else:
            self.compiled.append(command_portion)

    def _compile(self):
        self.compiled = []
        self._add_to_compile_list(self.command)
        self._add_to_compile_list(self.width)
        self._add_to_compile_list(self.height)
        self._add_to_compile_list(self.title)
        self._add_to_compile_list(self.type)
        self._add_to_compile_list(self.head)
        self._add_to_compile_list(self.body)
        try: self._additional_compile()
        except NoAdditionalCompile: pass

    def set_width(self, width):
        self.width = None
        raise NotImplementedError

    def set_height(self, height):
        self.height = None
        raise NotImplementedError

    def set_title(self, title):
        self.title = None
        raise NotImplementedError

    def _set_command(self, command):
        self.command = None
        raise NotImplementedError

    def _additional_compile(self):
        raise NoAdditionalCompile

    @abstractmethod
    def _do_show(self):
        pass

    def show(self):
        self._compile()
        return self._do_show()

class List(Dialog):
    @abstractmethod
    def __init__(self, title, list_type, columns):
        pass

    @abstractmethod
    def _do_add_row(self, array):
        pass

    @abstractmethod
    def _add_column(self, name):
        pass

    def add_row(self, checked, array):
        if len(array) + 1 != self.column_number:
            raise MenuException("Number of elements passed mismatch columns number:\n passed " + str(len(array) + 1) + " but " + str(self.column_number) + " needed.")

        self._do_add_row(checked, array)

        return self

    def hide_first_column(self):
        self._hide_first_column = True

    def show_first_column(self):
        self._hide_first_column = True

class Radiolist(List):
    @abstractmethod
    def __init__(self, title, columns):
        pass

class Checklist(List):
    @abstractmethod
    def __init__(self, title, columns, split_char = "|"):
        pass

    @property
    def split_char(self):
        return self._split_char

    @split_char.setter
    def split_char(self, split_char):
        self._split_char = split_char

    # override
    def show(self):
        self._compile()
        return self._do_show().split(self._split_char)

class SelectFile(Dialog):
    @abstractmethod
    def __init__(self, title):
        pass

class SelectDirectory(Dialog):
    @abstractmethod
    def __init__(self, title):
        pass

class SelectWritableDirectory(SelectDirectory):
    def __init__(self, title):
        super(SelectWritableDirectory, self).__init__(title)

    @property
    def error_dialog(self):
        return self._error_dialog

    @error_dialog.setter
    def error_dialog(self, error_dialog):
        self._error_dialog = error_dialog

    # override
    def show(self):
        self._compile()
        picked_dir = self._do_show()
        while not os.access(picked_dir, os.W_OK):
            self.error_dialog("Error", "Selected destination \"" + picked_dir + "\" is not writable.").show()
            picked_dir = self._do_show()
        return picked_dir

class ErrorDialog(Dialog):
    @abstractmethod
    def __init__(self, title, error_message):
        pass

class ConfirmDialog(Dialog):
    @abstractmethod
    def __init__(self, title, question, ok_label = None, cancel_label = None, end = "\n"):
        pass
    
    @abstractmethod
    def append_new_line(self, text = "", end = "\n"):
        pass

    def _handle_return(self, returned):
        if returned == True:
            if not (self.confirm_action is None) and callable(self.confirm_action):
                return self.confirm_action()
            else:
                return returned
        else:
            if not (self.cancel_action is None) and callable(self.cancel_action):
                return self.cancel_action()
            else:
                return returned

    def raise_on_canceled(self):
        self.on_canceled(raise_cancel)

    def on_confirmed(self, callback):
        self.confirm_action = callback

    def on_canceled(self, callback):
        self.cancel_action = callback
    
    # override
    def show(self):
        self._compile()
        returned = self._do_show() == 0
        return self._handle_return(returned)

class Progress(Dialog):
    @abstractmethod
    def __init__(self, title, status_string, process_to_monitor = None):
        pass

    def _add_process_to_monitor(self, process_to_monitor):
        self.monitored = process_to_monitor

    def wait_finish(self):
        try:
            self.monitored.wait()
        except Exception as e:
            MenuException(e)
    
    def is_still_running(self):
        try:
            return self.monitored.poll() is None
        except Exception as e:
            MenuException(e)

    def get_output(self):
        try:
            for stdout_line in iter(lambda: self.monitored.stdout.read(1), b''):
                yield stdout_line
            
            self.monitored.stdout.close()
        except Exception as e:
            MenuException(e)

    def get_returncode(self):
        if self.is_still_running(): return None
        return self.monitored.returncode
    
    def cancel(self):
        try:
            self.monitored.kill()
        except Exception as e:
            MenuException(e)
        else:
            raise MenuCancel("Operation canceled.")

    def monitor(self, process_to_monitor):
        if not isinstance(process_to_monitor, subprocess.Popen):
            raise raise_ex("Can't monitor this process.\nYou need to pass a 'subprocess.Popen'.")
        if process_to_monitor.stdout is None:
            raise raise_ex("Can't monitor this process.\nYou need to pass a 'subprocess.Popen' started with arg 'stdout=subprocess.PIPE'!")

        self._add_process_to_monitor(process_to_monitor)

        return self

    @abstractmethod
    def filter_process_output(self, decoded_output):
        pass

    def set_output_filter_function(self, function):
        self.filter_process_output = function

    # override
    def show(self):
        self._compile()
        self._do_show()
        return self.get_returncode()

class ProgressWait(Progress):
    def __init__(self, title, status_string, process_to_monitor = None):
        super(ProgressWait, self).__init__(title, status_string, process_to_monitor = None)


def byte_to_human_readable(number):
    result = float(number)
    order = 0
    while result / 1024 > 1.0 and order < 4:
        order += 1
        result = result / 1024
 
    result = round(result, 2)

    order_string = "B"
    if order == 1: order_string = "KiB"
    elif order == 2: order_string = "MiB"
    elif order == 3: order_string = "GiB"
    elif order == 4: order_string = "TiB"

    return str(result) + order_string