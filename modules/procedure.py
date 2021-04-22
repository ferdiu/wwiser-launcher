
import os
from .fake_launcher import FakeLauncherSettings

_DEBUG = bool(os.environ.get('DEBUG')) or FakeLauncherSettings.is_debug()
if _DEBUG:
    import traceback

class ProcedureStepCanceledException(Exception): pass
class ProcedureException(Exception): pass
class ProcedureCanceled(Exception): pass

class ProcedureNode(object):
    def __init__(self, id, function_to_call, function_args, sets_common = None, get_jumped_on_cancel = False):
        self.id = id
        self.func = function_to_call
        self.args = function_args
        self.sets_common = sets_common
        self.get_jumped_on_cancel = get_jumped_on_cancel
    
    def activate(self):
        if isinstance(self.args, tuple):
            real_args = ()
            for t in self.args:
                if isinstance(t, ProcedureFutureValue):
                    real_args += (t.get(),)
                else:
                    real_args += (t,)
            return self.func(*real_args)
        else:
            raise ProcedureException("Arguments should be touples, they are:" + str(type(self.args)))
    
    def sets_a_common_variable(self):
        return not (self.sets_common is None)

class ProcedureFutureValue(object):
    def __init__(self, l_function, tuple_arguments):
        self.l = l_function
        self.args = tuple_arguments
    
    def get(self):
        return (self.l)(*self.args)

EXIT_CODE = {
    "CANCELED": -1,
    "SUCCESS": 0,
    "ERROR": 1
}

class Procedure(object):

    def __init__(self, procedure_id, menu_queue = []):
        self.id = procedure_id
        self.menu_queue = menu_queue
        self.menu_stack = []
        self.menu_current = None
        self.common = {}
    
    def start(self):
        if self.is_started():
            print("Procedure " + self.id + " already started.")
        else:
            print("Starting procedure " + self.id + ".")
            self.menu_current = self.menu_queue.pop(0)
            return self._execute_current()

    def is_started(self):
        return not (self.menu_current is None)
    
    def set_common(self, obj):
        self.common = obj
        return self
    
    def get_common(self, key):
        if key in self.common:
            return self.common[key]
        else:
            return None
    
    def future_get_common(self, key):
        return ProcedureFutureValue(lambda key: self.get_common(key), (key,))

    def enqueue_menu(self, menu_node):
        self.menu_queue.append(menu_node)
        return self

    def _print_menu_queue(self):
        for m in self.menu_queue:
            print("- " + str(m.id))
    
    def _print_menu_current(self):
        print("> " + str(self.menu_current.id))
        
    def _print_menu_stack(self):
        for m in self.menu_stack:
            print("- " + str(m.id))

    def _print_procedure_status(self):
        print("# Procedure " + str(self.id) + " status:")
        self._print_menu_stack()
        self._print_menu_current()
        self._print_menu_queue()

    def _execute_next(self):
        self.menu_stack.append(self.menu_current)
        self.menu_current = None
        if len(self.menu_queue) == 0:
            print("Procedure " + self.id + " finished.")
            return self._exit(EXIT_CODE["SUCCESS"])
        self.menu_current = self.menu_queue.pop(0)
        return self._execute_current()

    def _execute_previous(self):
        self.menu_queue.insert(0, self.menu_current)
        self.menu_current = None
        if len(self.menu_stack) == 0:
            print("Procedure " + self.id + " canceled.")
            return self._exit(EXIT_CODE["CANCELED"])
        self.menu_current = self.menu_stack.pop()
        while self.menu_current.get_jumped_on_cancel:
            self.menu_queue.insert(0, self.menu_current)
            self.menu_current = self.menu_stack.pop()
        return self._execute_current()
    
    def _execute_current(self):
        if _DEBUG:
            self._print_procedure_status()
        returned_value = ""
        try:
            returned_value = self.menu_current.activate()
        except ProcedureStepCanceledException as ex:
            return self._execute_previous()
        except ProcedureException:
            if _DEBUG:
                print(traceback.format_exc())
            print("Procedure " + self.id + " canceled because an error occurred.")
            return self._exit(EXIT_CODE["ERROR"])
        else:
            if self.menu_current.sets_a_common_variable():
                self.common[self.menu_current.sets_common] = returned_value
            return self._execute_next()
    
    def _exit(self, code):
        while len(self.menu_stack) > 0:
            p_node = self.menu_stack.pop()
            del p_node
        while len(self.menu_queue) > 0:
            p_node = self.menu_queue.pop()
            del p_node
        del self.menu_stack
        del self.menu_current
        del self.menu_queue
        del self
        return code
