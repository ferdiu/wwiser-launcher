
import unittest
import subprocess
import os

from . import zenity as Menu
# from . import kdialog as Menu

test_directory = os.path.abspath(os.path.dirname(__file__)) + "/" + "test_dir"
test_unwritable = test_directory + "/unwritable"

class TestingUIImplementation(unittest.TestCase):
    def setUp(self):
        if not os.path.isdir(test_directory):
            os.makedirs(test_directory)
        if not os.path.isdir(test_unwritable):
            os.makedirs(test_unwritable)
        os.chmod(test_unwritable, 555)

    def tearDown(self):
        pass

    # CONFIRM DIALOG
    def test_confirm_dialog_ok(self):
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (OK)", "Press \"OK\" to make the test pass.", "OK", "Cancel")
        menu_confirm.show()

    def test_confirm_dialog_cancel(self):
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (CANCEL)", "Press \"Cancel\" to make the test pass.", "OK", "Cancel")
        try:
            menu_confirm.show()
        except Menu.Menu.MenuCancel:
            return
        raise Exception('test_confirm_dialog_cancel didn\'t raise a MenuCancel Exception')

    def test_confirm_dialog_on_confirmed(self):
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (ON CONFIRMED)", "Press \"OK\" to make the test pass.", "OK", "Cancel")
        menu_confirm.on_confirmed(lambda: "HELLO")
        menu_confirm.show()

    def test_confirm_dialog_on_canceled(self):
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (ON CANCELED)", "Press \"Cancel\" to make the test pass.", "OK", "Cancel")
        menu_confirm.on_canceled(lambda: "CANCELED")
        try:
            menu_confirm.show()
        except Menu.Menu.MenuCancel:
            return
        raise Exception('test_confirm_dialog_on_canceled didn\'t raise a MenuCancel Exception')

    def test_confirm_dialog_raise_on_cancel(self):
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (RAISE ON CANCELED)", "Press \"Cancel\" to make the test pass.", "OK", "Cancel")
        menu_confirm.raise_on_canceled()
        try:
            menu_confirm.show()
        except Menu.Menu.MenuCancel:
            pass
        except Menu.Menu.MenuCancel:
            return
        raise Exception('test_confirm_dialog_raise_on_cancel didn\'t raise a MenuCancel Exception')

    # PROGRESS
    def test_progress(self):
        progress_dialog = Menu.Progress("TEST - Progress", "Wait the process to finish.", subprocess.Popen(["/home/ferdiu/prova"], stdout=subprocess.PIPE)).show()
        print("Exited: " + str(progress_dialog))

    # SELECT DIRECTORY
    def test_select_directory_select(self):
        select_dir = Menu.SelectDirectory("TEST - SelectDirectory (PICK ONE)")
        select_dir.show()

    def test_select_directory_cancel(self):
        select_dir = Menu.SelectDirectory("TEST - SelectDirectory (CANCEL)")
        select_dir.show()

    # SELECT WRITABLE DIRECTORY
    def test_select_writable_directory_select(self):
        select_dir = Menu.SelectWritableDirectory("TEST - SelectWritableDirectory (PICK WRITABLE)")
        select_dir.show()

    def test_select_writable_directory_select_cancel(self):
        select_dir = Menu.SelectWritableDirectory("TEST - SelectWritableDirectory (CANCEL)")
        select_dir.show()

    def test_select_writable_directory_select_select_unwritable(self):
        select_dir = Menu.SelectWritableDirectory("TEST - SelectWritableDirectory (PICK UNWRITABLE)")
        select_dir.show()

    # ERROR DIALOG
    def test_error_dialog_ok(self):
        Menu.ErrorDialog("TEST - ErrorDialog", "Press \"OK\".").show()

    def test_error_dialog_close(self):
        Menu.ErrorDialog("TEST - ErrorDialog", "Close this window or hit \"Cancel\".").show()

    # RADIOLIST
    def test_radiolist_ok(self):
        menu_list = Menu.Radiolist("TEST - Radiolist (OK)", [ "ID", "Name" ])
        menu_list.add_row(True, [ "marco", "Marco (selected to pass)" ])
        menu_list.add_row(True, [ "francesco", "Francesco (selected to pass)" ])
        menu_list.show()

    def test_radiolist_cancel(self):
        menu_list = Menu.Radiolist("TEST - Radiolist (CANCEL)", [ "ID", "Name" ])
        menu_list.add_row(True, [ "marco", "Press \"Cancel\"" ])
        menu_list.add_row(True, [ "francesco", "Press \"Cancel\"" ])
        menu_list.show()

    # CHECKLIST
    def test_checklist(self):
        menu_list = Menu.Checklist("TEST - Checklist (OK)", [ "ID", "Nome" ])
        menu_list.add_row(True, [ "marco", "Marco (selected to pass)" ])
        menu_list.add_row(False, [ "francesco", "Francesco" ])
        menu_list.show()

    def test_checklist_cancel(self):
        menu_list = Menu.Radiolist("TEST - Radiolist (CANCEL)", [ "ID", "Name" ])
        menu_list.add_row(True, [ "marco", "Press \"Cancel\"" ])
        menu_list.add_row(False, [ "francesco", "Press \"Cancel\"" ])
        menu_list.show()


if __name__ == '__main__':
    unittest.main()