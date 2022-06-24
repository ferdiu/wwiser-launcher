
import os
import subprocess
import json
from sys import stdout

from .fake_launcher import FakeLauncher, FakeLauncherSettings, BundleType, FakeLauncherException, PackagesType, SourceCodeLevel
from .procedure import Procedure, ProcedureException, ProcedureStepCanceledException, ProcedureNode
from .ui import zenity as Menu
from .ui.common import ErrorDialog, byte_to_human_readable, MenuException, MenuCancel

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
    for b in FakeLauncher.get_all_available_bundles_for_wwise_version(installation_info["bundle"]["version"], BundleType.plugin):
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
        os.makedirs(download_destination)
    except:
        pass

    try:
        os.makedirs(download_destination + "/bundle")
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
    confirm_dialog = Menu.ConfirmDialog("Error checking files", "Following files didn't pass sha1 sum-check:\n")
    problematic_files = []

    for f in installation_info["file_list"]:
        sha1sum_output = subprocess.check_output([ "sha1sum", bundle_directory + "/" + f["id"] ]).decode('utf-8').split(" ")[0]
        if sha1sum_output == f["sha1"]:
            print("File " + f["id"] + ": OK")
        else:
            print("File " + f["id"] + ": FAIL")
            problematic_files.append(f)
            confirm_dialog.append_new_line("- " + f["id"])
    
    confirm_dialog.append_new_line("\nDo you want to continue the installation without them?")
    confirm_dialog.append_new_line("\nNote: this may lead to unstable and incomplete installation.")

    if len(problematic_files) > 0: 
        try:
            if confirm_dialog.show():
                print("Continuing installation anyway.")
                i = len(installation_info["file_list"]) - 1
                while i >= 0:
                    if installation_info["file_list"][i] in problematic_files:
                        os.remove(bundle_directory + "/" + installation_info["file_list"].pop(i)["id"])
                    i -= 1
            else:
                raise ProcedureStepCanceledException
        except MenuCancel as e:
            raise ProcedureStepCanceledException
        except FakeLauncherException and MenuException as e:
            raise ProcedureException(e)


def _select_install_destination(installation_info):
    # TODO make this a selection instead of prefixed path
    os.makedirs(installation_info["install_path"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["install-entry"]), exist_ok=True)

def _extract_archives(installation_info):
    bundle_directory = installation_info["download_directory"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["install-entry"]) + "/bundle"

    for (i, f) in enumerate(installation_info["file_list"]):
        # TODO show progress
        x_process = FakeLauncher.extract_archive(bundle_directory + "/" + f["id"], dest_path = installation_info["install_path"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["install-entry"]))
        x_process.wait()

def _fix_directories(installation_info):
    #Find problematic directories
    find_proc = subprocess.Popen([
        "find",
        installation_info["install_path"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["install-entry"]),
        "-type", "d"
    ], stdout=subprocess.PIPE, universal_newlines=True)
    sort_proc = subprocess.Popen([
        "sort", "-f"
    ], stdin=find_proc.stdout, stdout=subprocess.PIPE, universal_newlines=True)
    uniq_proc = subprocess.Popen([
        "uniq", "-id"
    ], stdin=sort_proc.stdout, stdout=subprocess.PIPE, universal_newlines=True)

    output, errors = uniq_proc.communicate()
    problematic_dirs = output.split("\n")
    # Remove empty strings
    problematic_dirs = [ d for d in problematic_dirs if len(d) > 0 ]

    fixed = 0
    for dir in problematic_dirs:
        fixed += 1
        alternatives = subprocess.check_output([
            "find",
            installation_info["install_path"] + "/Wwise " + FakeLauncher.get_version_as_string(installation_info["install-entry"]),
            "-ipath", dir,
            "-type", "d",
        ], universal_newlines=True).split("\n")
        alternatives = [ d for d in alternatives if len(d) > 0 ]
        # Select the "most lower case" directory
        selected = max(alternatives)
        for alt in alternatives:
            if alt == selected: continue
            for f in os.listdir(alt):
                os.rename(alt + "/" + f, selected + "/" + f)
            os.rmdir(alt)

    if fixed > 0:
        _fix_directories(installation_info)

def _generate_wwise_authoring_app_launch_script(installation_info):
    list_menu = Menu.Radiolist("Install Authoring ", [ "ID", "Directory" ])
    list_menu.add_row(True, [os.environ.get("HOME"), "Place it in the home to move it later" ])
    wwise_version = FakeLauncher.get_version_as_string(installation_info["install-entry"])

    for d in os.environ.get("PATH").split(":"):
        if os.access(d, os.W_OK):
            list_menu.add_row(False, [ d, d ])

    try:
        selected_dir = list_menu.show()
        if len(selected_dir) > 0:
            with open(selected_dir + "/wwise_" + wwise_version, "w") as file:
                file.write(FakeLauncher.authoring_app_launcher(installation_info["install_path"].replace(os.environ.get("HOME"), "${HOME}"), wwise_version))
                file.close()
                os.chmod(selected_dir + "/wwise_" + wwise_version, 0o755)
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

def _pick_offline_install_directory(installation_info):
    try:
        dir_selection_menu = Menu.SelectFile("Pick install-entry.json file", "install-entry.json")
        install_entry_file_path = dir_selection_menu.show()
        wwise_install_dir = install_entry_file_path.replace("/bundle/install-entry.json", "")
        with open(install_entry_file_path) as inst_entry:
            installation_info["install-entry"] = json.loads(inst_entry.read())
        if installation_info["install-entry"]["type"] != "wwise":
            raise ProcedureException("Not a Wwise Authoring App installation!")

        # TODO use bundle to perform checks on files
        if os.path.isfile(wwise_install_dir + "/bundle/bundle.json"):
            with open(wwise_install_dir + "/bundle/bundle.json") as bundle_file:
                installation_info["bundle"] = json.loads(bundle_file.read())

        installation_info["file_list"] = [ { "id": tar } for tar in os.listdir(wwise_install_dir + "/bundle") if tar.endswith(".tar.xz") ]
        print(installation_info["file_list"])

        if len(installation_info["bundle"]):pass # TODO check files

        installation_info["download_directory"] = wwise_install_dir.replace("/Wwise " + FakeLauncher.get_version_as_string(installation_info["install-entry"]), "")
    except MenuCancel as e:
        raise ProcedureStepCanceledException
    except FakeLauncherException and MenuException as e:
        raise ProcedureException(e)

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
        "download_directory": "",
        "install_path": os.environ.get("HOME") + "/.wine/drive_c/Program Files (x86)/Audiokinetic"
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
            _download_files, (installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "WriteInfoFiles",
            _write_bundle_and_install_entry, (installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "CheckDownloadedArchives",
            _check_downloaded_files, (installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "SelectInstallationDestination",
            _select_install_destination, (installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "ExtractArchives",
            _extract_archives, (installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "FixDirectories",
            _fix_directories, (installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "GenerateWwiseAuthoringAppScript",
            _generate_wwise_authoring_app_launch_script, (installation_procedure.common,))
    )
    return installation_procedure

def get_offline_installation_procedure():
    offline_installation_procedure = Procedure("offline installation")
    offline_installation_procedure.set_common({
        "bundle": {},
        "install-entry": {},
        "file_list": [],
        "download_directory": "",
        "install_path": os.environ.get("HOME") + "/.wine/drive_c/Program Files (x86)/Audiokinetic"
    }).enqueue_menu(
        ProcedureNode(
            "PickInstallationFromDrive",
            _pick_offline_install_directory, (offline_installation_procedure.common,))
    ).enqueue_menu(
        ProcedureNode(
            "SelectInstallationDestination",
            _select_install_destination, (offline_installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "ExtractArchives",
            _extract_archives, (offline_installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "FixDirectories",
            _fix_directories, (offline_installation_procedure.common,),
            get_jumped_on_cancel=True)
    ).enqueue_menu(
        ProcedureNode(
            "GenerateWwiseAuthoringAppScript",
            _generate_wwise_authoring_app_launch_script, (offline_installation_procedure.common,))
    )
    # Select directory containing offline installation
    # Check it is a wwise install-entry.json
    # Get version

    return offline_installation_procedure