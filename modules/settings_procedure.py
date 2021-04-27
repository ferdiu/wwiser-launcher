
from .fake_launcher import FakeLauncher, FakeLauncherSettings, Setting, FakeLauncherException
from .procedure import Procedure, ProcedureException, ProcedureStepCanceledException, ProcedureNode
from .ui import zenity as Menu
from .ui.common import MenuException, MenuCancel

def _show_settings_menu():
    list_menu = Menu.Checklist("Settings", [ "ID", "", "" ])
    for k in FakeLauncherSettings.settings.keys():
        setting = FakeLauncherSettings.settings[k]
        list_menu.add_row(
            setting.value,
            [ 
                setting.id,
                setting.name,
                setting.description 
            ])

    list_menu.add_row(
        False,
        [ 
            "reset_all",
            "Reset all",
            "Reset all settings to default values (other checks will be ignored)." 
        ])

    try:
        return list_menu.show()
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

def _apply_settings(common):
    selected = common["selected"]

    try:
        if "reset_all" in selected:
            confirm = Menu.ConfirmDialog("Reset", "Are you sure you want to reset all settings to default values?").show()
            if confirm:
                FakeLauncherSettings.reset_all()
            else:
                raise MenuCancel
        else:
            for k in FakeLauncherSettings.settings.keys():
                # if key was selected and its default value was not true save it in the file
                if k in selected and FakeLauncherSettings.settings[k].default != True:
                    FakeLauncherSettings.settings[k].set_to(True)
                # if key was not selected and its default value was not false save it in the file
                elif not k in selected and FakeLauncherSettings.settings[k].default != False:
                    FakeLauncherSettings.settings[k].set_to(False)
        FakeLauncherSettings.save()
        FakeLauncherSettings.load()

    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)


def get_settings_procedure():
    settings_procedure = Procedure("settings")
    settings_procedure.set_common({
        "selected": [],
    }).enqueue_menu(
        ProcedureNode(
            "ShowSettings",
            _show_settings_menu, (),
            "selected")
    ).enqueue_menu(
        ProcedureNode(
            "ApplySettings",
            _apply_settings, (settings_procedure.common,))
    )
    return settings_procedure
