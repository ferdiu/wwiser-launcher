
import unittest
import subprocess
import os

from . import zenity as Menu

test_directory = os.path.abspath(os.path.dirname(__file__)) + "/" + "test_dir"
test_unwritable = test_directory + "/unwritable"

class TestingUIImplementation(unittest.TestCase):
    def setUp(self):
        os.makedirs(test_directory)
        os.makedirs(test_unwritable)
        os.chmod(test_unwritable, 555)

    def tearDown(self):
        pass

    # CONFIRM DIALOG
    def test_confirm_dialog_ok():
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (OK)", "Press \"OK\" to make the test pass.", "OK", "Cancel")
        menu_confirm.show()

    def test_confirm_dialog_cancel():
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (CANCEL)", "Press \"Cancel\" to make the test pass.", "OK", "Cancel")
        menu_confirm.show()

    def test_confirm_dialog_on_confirmed():
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (ON CONFIRMED)", "Press \"OK\" to make the test pass.", "OK", "Cancel")
        menu_confirm.on_confirmed(lambda: "HELLO")
        menu_confirm.show()

    def test_confirm_dialog_on_canceled():
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (ON CANCELED)", "Press \"Cancel\" to make the test pass.", "OK", "Cancel")
        menu_confirm.on_canceled(lambda: "CANCELED")
        menu_confirm.show()

    def test_confirm_dialog_raise_on_cancel():
        menu_confirm = Menu.ConfirmDialog("TEST - ConfirmDialog (RAISE ON CANCELED)", "Press \"Cancel\" to make the test pass.", "OK", "Cancel")
        menu_confirm.raise_on_canceled()
        menu_confirm.show()

    # PROGRESS
    def test_progress():
        progress_dialog = Menu.Progress("TEST - Progress", "Wait the process to finish.", subprocess.Popen(["/home/ferdiu/prova"], stdout=subprocess.PIPE)).show()
        print("Exited: " + str(progress_dialog))

    # SELECT DIRECTORY
    def test_select_directory_select():
        select_dir = Menu.SelectDirectory("TEST - SelectDirectory (PICK ONE)")
        select_dir.show()

    def test_select_directory_cancel():
        select_dir = Menu.SelectDirectory("TEST - SelectDirectory (CANCEL)")
        select_dir.show()

    # SELECT WRITABLE DIRECTORY
    def test_select_writable_directory_select():
        select_dir = Menu.SelectWritableDirectory("TEST - SelectWritableDirectory (PICK WRITABLE)")
        select_dir.show()

    def test_select_writable_directory_select_cancel():
        select_dir = Menu.SelectWritableDirectory("TEST - SelectWritableDirectory (CANCEL)")
        select_dir.show()

    def test_select_writable_directory_select_select_unwritable():
        select_dir = Menu.SelectWritableDirectory("TEST - SelectWritableDirectory (PICK UNWRITABLE)")
        select_dir.show()

    # ERROR DIALOG
    def test_error_dialog_ok():
        Menu.ErrorDialog("TEST - ErrorDialog", "Press \"OK\".").show()

    def test_error_dialog_close():
        Menu.ErrorDialog("TEST - ErrorDialog", "Close this window or hit \"Cancel\".").show()

    # RADIOLIST
    def test_radiolist_ok():
        menu_list = Menu.Radiolist("TEST - Radiolist (OK)", [ "ID", "Name" ])
        menu_list.add_row(True, [ "marco", "Marco (selected to pass)" ])
        menu_list.add_row(True, [ "francesco", "Francesco (selected to pass)" ])
        menu_list.show()

    def test_radiolist_cancel():
        menu_list = Menu.Radiolist("TEST - Radiolist (CANCEL)", [ "ID", "Name" ])
        menu_list.add_row(True, [ "marco", "Press \"Cancel\"" ])
        menu_list.add_row(True, [ "francesco", "Press \"Cancel\"" ])
        menu_list.show()

    # CHECKLIST
    def test_checklist():
        menu_list = Menu.Checklist("TEST - Checklist (OK)", [ "ID", "Nome" ])
        menu_list.add_row(True, [ "marco", "Marco (selected to pass)" ])
        menu_list.add_row(False, [ "francesco", "Francesco" ])
        menu_list.show()

    def test_checklist_cancel():
        menu_list = Menu.Radiolist("TEST - Radiolist (CANCEL)", [ "ID", "Name" ])
        menu_list.add_row(True, [ "marco", "Press \"Cancel\"" ])
        menu_list.add_row(False, [ "francesco", "Press \"Cancel\"" ])
        menu_list.show()


if __name__ == '__main__':
    unittest.main()