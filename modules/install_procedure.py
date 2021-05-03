
import os
import subprocess
import json

from .fake_launcher import FakeLauncher, FakeLauncherSettings, BundleType, FakeLauncherException, PackagesType, SourceCodeLevel
from .procedure import Procedure, ProcedureException, ProcedureStepCanceledException, ProcedureNode
from .ui import zenity as Menu
from .ui.common import byte_to_human_readable, MenuException, MenuCancel

if FakeLauncherSettings.is_debug():
    import traceback

def _pick_wwise_version(bundles):
    list_menu = Menu.Radiolist("Pick a Wwise version", [ "ID", "Wwise version" ])
    i = 0
    for b in FakeLauncher.get_all_bundles_of_type(BundleType.wwise):
        version_id = FakeLauncher.get_version_as_string(b)

        list_menu.add_row(i == 0, [ b["id"], "Wwise " + version_id ])
        i += 1

    try:
        return FakeLauncher.get_bundle_by_id(list_menu.show())
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

def _init_install_entry(installation_info):
    try:
        return FakeLauncher.init_install_entry(installation_info["bundle"]["id"])
    except FakeLauncherException as e:
        raise ProcedureException(e)

def _pick_packages_from_bundle(installation_info):
    list_menu = Menu.Checklist("Packages selection", [ "ID", "Packages", "Description" ])
    for value in FakeLauncher.get_values_in_group(installation_info["bundle"], "Packages"):
        if FakeLauncher.is_value_visible(value):
            list_menu.add_row(
                FakeLauncher.is_value_checked(value),
                [ 
                    FakeLauncher.get_value_id(value),
                    FakeLauncher.get_value_display_name(value),
                    FakeLauncher.get_value_description(value) 
                ])
    try:
        return list_menu.show()
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

def _pick_deployment_platforms(installation_info):
    list_menu = Menu.Checklist("Deployment Platforms", [ "ID", "Deployment Platforms" ])
    for value in FakeLauncher.get_values_in_group(installation_info["bundle"], "DeploymentPlatforms"):
        list_menu.add_row(
            FakeLauncher.is_value_checked(value) or FakeLauncher.get_value_id(value) == "Linux",
            [ 
                FakeLauncher.get_value_id(value),
                FakeLauncher.get_value_display_name(value)
            ])

    try:
        return list_menu.show()
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

def _pick_plugins(installation_info):
    list_menu = Menu.Checklist("Plugins", [ "ID", "Plugin", "Labels", "Description" ])
    for b in FakeLauncher.get_all_bundles_for_wwise_version(installation_info["bundle"]["version"], BundleType.plugin):
        if FakeLauncher.is_value_visible(b):
            list_menu.add_row(
                FakeLauncher.is_value_checked(b),
                [
                    FakeLauncher.get_value_id(b),
                    FakeLauncher.get_value_display_name(b) or FakeLauncher.get_value_name(b),
                    FakeLauncher.get_value_labels_as_string(b),
                    FakeLauncher.get_value_description(b)
                ]
            )

    try:
        return list_menu.show()
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

def _file_infos_matches_installation_infos(installation_info, f):
    if "groups" in f and isinstance(f["groups"], list):
        num_matched = 0
        for g in f["groups"]:
            if "groupId" in g and "groupValueId" in g:
                if g["groupId"] in installation_info and g["groupValueId"] in installation_info[g["groupId"]]:
                    # If is a doc and doc was not selected, return False
                    if "Documentation" in f["id"] and not ("Documentation" in installation_info["Packages"]):
                        return False
                    num_matched += 1
        # if all matched then this file is a candidate for download
        return num_matched == len(f["groups"])
    else:
        return False

def _pick_files_to_download(installation_info):
    array = []

    # Pick packages
    if not ("files" in installation_info["bundle"]):
        raise Exception("The selected bundle has no downloadable files.")

    for f in FakeLauncher.get_files_in_bundle(installation_info["bundle"]):
        if FakeLauncher.is_file_downloadable(f) and _file_infos_matches_installation_infos(installation_info, f):
            array.append(f)

    # Pick plugins
    for p in FakeLauncher.get_all_bundles_for_wwise_version(installation_info["bundle"]["version"], BundleType.plugin):
        if p["id"] in installation_info["plugins"]: # Filter the ones selected
            if "files" in p and isinstance(p["files"], list):
                for f in p["files"]:
                    if FakeLauncher.is_file_downloadable(f) and \
                       _file_infos_matches_installation_infos(installation_info, f):
                        array.append(f)

    return array

def _pick_download_directory(installation_info):
    if FakeLauncherSettings.settings["ask_cache"].value:
        try:
            dir_selection_menu = Menu.SelectWritableDirectory("Choose where you want to create the installation")
            return dir_selection_menu.show()
        except MenuCancel as e:
            raise ProcedureStepCanceledException
        except FakeLauncherException and MenuException as e:
            raise ProcedureException(e)
    else:
        return FakeLauncher.cache_dir

def _confirm_install(installation_info):
    confirm_dialog = Menu.ConfirmDialog("Do you want to proceed with installation?", "The following packages will be installed:")

    for f in installation_info["file_list"]:
        confirm_dialog.append_new_line("- " + f["id"])

    confirm_dialog.append_new_line()

    installation_info["download_size"] = 0
    installation_info["installed_size"] = 0
    for f in installation_info["file_list"]:
        if "size" in f:
            installation_info["download_size"] += f["size"]
        if "uncompressedSize" in f:
            installation_info["installed_size"] += f["uncompressedSize"]

    confirm_dialog.append_new_line()
    confirm_dialog.append_new_line("The necessary packages will be downloaded in")
    confirm_dialog.append_new_line(str(installation_info["download_directory"]))
    confirm_dialog.append_new_line()

    confirm_dialog.append_new_line("Need to download " + byte_to_human_readable(installation_info["download_size"]) + ".")
    confirm_dialog.append_new_line("Install will take " + byte_to_human_readable(installation_info["installed_size"]) + ".")

    confirm_dialog.raise_on_canceled()

    try:
        return confirm_dialog.show()
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

def _download_files(installation_info):
    download_destination = installation_info["download_directory"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["bundle"])

    # It is safe to ignore this errors because the menu already selected a valid destination
    try:
        os.mkdir(download_destination)
    except:
        pass

    try:
        os.mkdir(download_destination + "/bundle")
    except:
        pass

    for f in installation_info["file_list"]:
        try:
            dl_process = FakeLauncher.download_file(f, download_destination + "/bundle", force = False)
            if not (dl_process is None):
                dl_process.wait_finish()
        except MenuCancel as e:
            raise ProcedureStepCanceledException
        except FakeLauncherException and MenuException as e:
            raise ProcedureException(e)

def _write_bundle_and_install_entry(installation_info):
    bundle_directory = installation_info["download_directory"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["bundle"]) + "/bundle"
    with open(bundle_directory + "/install-entry.json", "w+") as inst_entry:
        inst_entry.write(json.dumps(installation_info["install-entry"]))
    with open(bundle_directory + "/bundle.json", "w+") as inst_entry:
        inst_entry.write(json.dumps(installation_info["bundle"]))

def _check_downloaded_files(installation_info):
    bundle_directory = installation_info["download_directory"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["bundle"]) + "/bundle"

    for f in installation_info["file_list"]:
        sha1sum_output = subprocess.check_output([ "sha1sum", bundle_directory + "/" + f["id"] ]).decode('utf-8').split(" ")[0]
        if sha1sum_output == f["sha1"]:
            print("File " + f["id"] + ": OK")
        else:
            print("File " + f["id"] + ": FAIL")

def get_installation_procedure():
    installation_procedure = Procedure("installation")
    installation_procedure.set_common({
        "bundle": {},
        "install-entry": {},
        "AuthoringPlatforms": [ "Win32", "x64" ],
        "AuthoringOS": [ "Windows" ],
        "SourceCodeLevel": [ SourceCodeLevel.level2, SourceCodeLevel.level3 ],
        "Packages": [],
        "DeploymentPlatforms": [],
        "plugins": [],
        "download_size": 0,
        "installed_size": 0,
        "file_list": [],
        "download_directory": ""
    }).enqueue_menu(
        ProcedureNode(
            "PickWwiseVersion",
            _pick_wwise_version, (FakeLauncher.bundles,),
            "bundle")
    ).enqueue_menu(
        ProcedureNode(
            "InitInstallEntry",
            _init_install_entry, (installation_procedure.common,),
            "install-entry", get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "PickPackagesFromBundles",
            _pick_packages_from_bundle, (installation_procedure.common,),
            "Packages")
    ).enqueue_menu(
        ProcedureNode(
            "PickDeploymentPlatforms",
            _pick_deployment_platforms, (installation_procedure.common,),
            "DeploymentPlatforms")
    ).enqueue_menu(
        ProcedureNode(
            "PickPlugins",
            _pick_plugins, (installation_procedure.common,),
            "plugins")
    ).enqueue_menu(
        ProcedureNode(
            "PickFilesToDownload",
            _pick_files_to_download, (installation_procedure.common,),
            "file_list", get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "SelectDownloadDirectory",
            _pick_download_directory, (installation_procedure.common,),
            "download_directory", get_jumped_on_cancel=not FakeLauncherSettings.settings["ask_cache"].value)
    ).enqueue_menu(
        ProcedureNode(
            "ConfirmInstallation",
            _confirm_install, (installation_procedure.common,))
    ).enqueue_menu(
        ProcedureNode(
            "DownloadArchives",
            _download_files, (installation_procedure.common,))
    ).enqueue_menu(
        ProcedureNode(
            "WriteInfoFiles",
            _write_bundle_and_install_entry, (installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "CheckDownloadedArchives",
            _check_downloaded_files, (installation_procedure.common,))
    )
    return installation_procedure
