#!/usr/bin/python3

import os
import subprocess

from modules.fake_launcher import FakeLauncher as Launcher, FakeLauncherSettings as Settings
from modules.ui.common import MenuCancel, MenuException
from modules.ui import zenity as Menu

# Import procedures
from modules.install_procedure import get_installation_procedure, get_offline_installation_procedure
from modules.apply_unity_integration_procedure import get_unity_integration_procedure
from modules.settings_procedure import get_settings_procedure

# Initialize globals
_DEBUG = bool(os.environ.get('DEBUG'))
wwiser_launcher_base_directory = os.path.abspath(os.path.dirname(__file__))

PROCEDURES = {
    "login": Menu.ErrorDialog("Not implemented.", "This procedure is still not implemented."),
    "installation": get_installation_procedure,
    "offline_installation": get_offline_installation_procedure,
    "unity_integration": get_unity_integration_procedure,
    "unreal_integration": Menu.ErrorDialog("Not implemented.", "This procedure is still not implemented."),
    "godot_integration": Menu.ErrorDialog("Not implemented.", "This procedure is still not implemented."),
    "settings": get_settings_procedure
}

def show_main_menu():
    return Menu.Radiolist("wwiser launcher - " + Launcher.u_id, [ "ID", "" ])\
        .add_row(True, [ "login", "Login [NOT IMPLEMENTED]" ])\
        .add_row(False, [ "installation", "Install Packages" ])\
        .add_row(False, [ "offline_installation", "Install Packages (Offline)" ])\
        .add_row(False, [ "unity_integration", "Apply Unity Integration" ])\
        .add_row(False, [ "unreal_integration", "Apply Unreal Integration [NOT IMPLEMENTED]" ])\
        .add_row(False, [ "godot_integration", "Apply Godot Integration [NOT IMPLEMENTED]" ])\
        .add_row(False, [ "settings", "Settings" ])\
        .show()

def initialize():
    try:
        Settings.load()
        if _DEBUG:
            Settings.settings["debug"].value = True
        Launcher.init()
        if Settings.is_debug():
            print("wwiser-launcher installation path: " + wwiser_launcher_base_directory)
        Launcher.wwiser_launcher_location = wwiser_launcher_base_directory
    except Exception as e:
        print("Couldn't initialize the launcher.")
        print(e)
        quit(1)

def start_wwiser_launcher():
    try:
        result = PROCEDURES[show_main_menu()]
        if issubclass(result.__class__, Menu.Dialog):
            result.show()
        elif callable(result):
            result().start()
        del result
        result = None
        del result
    except MenuCancel as e:
        quit(0)
    except MenuException as e:
        Menu.ErrorDialog("wwise-launcher", "An unrecoverable error occurred in the procedure. Quitting.")
        quit(1)

if __name__ == "__main__":
    initialize()
    while True:
        start_wwiser_launcher()
