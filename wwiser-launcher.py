#!/usr/bin/python3.7

import os

from modules.fake_launcher import FakeLauncher as Launcher
from modules.ui.common import MenuCancel, MenuException
from modules.ui import zenity as Menu
from modules.procedure import Procedure

# Import procedures
from modules.install_procedure import get_installation_procedure

# Initialize globals
_DEBUG = bool(os.environ.get('DEBUG'))
wwiser_launcher_base_directory = os.path.abspath(os.path.dirname(__file__))

PROCEDURES = {
    "login": Menu.ErrorDialog("Not implemented.", "This procedure is still not implemented."),
    "installation": get_installation_procedure(),
    "unity_integration": Menu.ErrorDialog("Not implemented.", "This procedure is still not implemented."),
    "unreal_integration": Menu.ErrorDialog("Not implemented.", "This procedure is still not implemented."),
    "godot_integration": Menu.ErrorDialog("Not implemented.", "This procedure is still not implemented.")
}

def show_main_menu():
    return Menu.Radiolist("wwiser launcher - " + Launcher.u_id, [ "ID", "" ])\
        .add_row(True, [ "login", "Login" ])\
        .add_row(False, [ "installation", "Install Packages" ])\
        .add_row(False, [ "unity_integration", "Apply Unity Integration" ])\
        .add_row(False, [ "unreal_integration", "Apply Unreal Integration" ])\
        .add_row(False, [ "godot_integration", "Apply Godot Integration" ])\
        .show()

def initialize():
    try:
        Launcher.init()
        if _DEBUG:
            print("wwiser-launcher installation path: " + wwiser_launcher_base_directory)
    except Exception as e:
        print("Couldn't initialize the launcher.")
        print(e)
        quit(1)

def start_wwiser_launcher():
    try:
        result = PROCEDURES[show_main_menu()]
        if issubclass(result.__class__, Menu.Dialog):
            result.show()
        elif isinstance(result, Procedure):
            print("Starting procedure")
            result.start()
    except MenuCancel as e:
        quit(0)
    except MenuException as e:
        Menu.ErrorDialog("wwise-launcher", "An unrecoverable error occurred in the procedure. Quitting.")
        quit(1)

if __name__ == "__main__":
    initialize()
    while True:
        start_wwiser_launcher()
