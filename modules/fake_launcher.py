
import os
import json
import base64
import subprocess
import sys
import yaml
import pathlib

from .download_manager.wget import Wget as Downloader

supported_unity_integration_versions = [ 18, 19 ]

class BundleType(object): # these are the equivalent of Categories of the real Wwise Launcher
    wwise = "wwise"
    sample = "sample"
    unity_integration = "UnityIntegration"
    unreal_integration = "UnrealIntegration"
    plugin = "plugin"
    launcher = "WwiseLauncher"

    @staticmethod
    def get_all():
        return [ BundleType.wwise, BundleType.sample, BundleType.unity_integration, BundleType.unreal_integration, BundleType.plugin, BundleType.launcher ]

class PackagesType(object):
    sample_project = "SampleProject"
    limbo = "Limbo"
    cube = "Cube"
    game_simulator = "GameSimulator"
    source_code = "SourceCode"
    docutation = "Documentation"
    sdk = "SDK"
    ltx = "LTX"
    authoring_debug = "AuthoringDebug"
    authoring = "Authoring"
    #
    unity_integration = "Unity"
    integration_extension = "Extensions"

class SourceCodeLevel(object):
    level2 = "Level2"
    level3 = "Level3"

class FakeLauncherException(Exception):
    pass

class Setting:
    def __init__(self, id, name, description, default, modified = False):
        self.id = id
        self.value = default
        self.name = name
        self.description = description
        self.default = default
        self.modifiled = modified
    
    def is_modified(self):
        return self.modifiled

    def set_to(self, boolean):
        self.value = boolean
        self.modifiled = True
    
    def reset(self):
        self.value = self.default
        self.modifiled = False
    
    def get_as_tuple(self):
        if not self.modifiled: return None
        return (self.id, self.value)

class FakeLauncherSettings:
    config_file_name = "settings.json"
    settings = {
        "ask_cache": Setting("ask_cache", "Ask where to cache downloaded files", "If this is turned on the launcher will ask where to place downloaded files before starting downloading them.", False),
        "debug": Setting("debug", "Debug mode", "Enable debugging.", False),
        "dev": Setting("dev", "Developer mode", "Enable developer mode.", False)
    }

    @staticmethod
    def save_file_exists():
        return os.path.isfile(FakeLauncher.config_dir + "/" + FakeLauncherSettings.config_file_name)

    @staticmethod
    def reset_all():
        for k in FakeLauncherSettings.settings.keys():
            FakeLauncherSettings.settings[k].reset()

    @staticmethod
    def save():
        dict = {}
        for k in FakeLauncherSettings.settings.keys():
            tup = FakeLauncherSettings.settings[k].get_as_tuple()
            if tup is not None:
                dict[tup[0]] = tup[1]

        with open(FakeLauncher.config_dir + "/" + FakeLauncherSettings.config_file_name, "w") as file:
            json.dump(dict, file, indent=2)
    
    @staticmethod
    def _apply_changes(settings_dict):
        for k in settings_dict.keys():
            if k in FakeLauncherSettings.settings:
                FakeLauncherSettings.settings[k].value = settings_dict[k]
            else:
                raise FakeLauncherException("There is no setting with id " + str(k))

    @staticmethod
    def load():
        FakeLauncherSettings.reset_all()

        if not FakeLauncherSettings.save_file_exists():
            if "debug" in FakeLauncherSettings.settings and FakeLauncherSettings.is_debug():
                print("No settings were saved. Nothing to load.")
            return
        
        with open(FakeLauncher.config_dir + "/" + FakeLauncherSettings.config_file_name, "r") as file:
            saved_settings = json.loads(file.read())
            FakeLauncherSettings._apply_changes(saved_settings)

    @staticmethod
    def is_debug():
        return FakeLauncherSettings.settings["debug"].value

if FakeLauncherSettings.is_debug():
    import traceback

class FakeLauncher(object):
    wwiser_launcher_location = ""
    config_dir = os.environ.get("HOME") + "/.config/wwiser-launcher"
    cache_dir = os.environ.get("HOME") + "/.cache/wwiser-launcher"
    bundles_dir = config_dir + "/bundles"

    # It was necessary to hardcode a version to retrieve a newer version
    version = {
        "year": 2020,
        "major": 3,
        "minor": 1,
        "build": 717
    }
    platform = "windows"
    jwt = ""
    jwt_location = config_dir + "/jwt.txt"

    most_recent_launcher = {}

    bundles = {}
    plugins = []

    pubkey="""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnAYv/1xDhJ39iT7Ftzcv
zXmhZRHkw5fbMPvz65z0Zh30yZCCmi5RZ0ds5kLcNdov0cdRkhPkWGkWe9/G+dkX
54DRMdvgIcuvmpAgxKz3re1vuTZHvz1DR2sy5FpSPV6lsX3CRLpaXzEo9fgYdqyB
cnqeOaq1byeNTMp2uRUF84NzkH2A3x6Vxx6pThdVMAVKbvPUhEtSBARAKxQstCkQ
ut8FlvQm2RgJrwbmXQfloz4h7uPwaM2jD2eApCfXHK05xh+1zMWFu6oqhqkfKUIK
GceEwONPkd039fwirfgKjbD5iGli3AuNn6PFVqyK0tcG/qYhjNVtJLCsHSmHyipD
rQIDAQAB
-----END PUBLIC KEY-----"""

    u_id = ""

    @staticmethod
    def authoring_app_launcher(install_path, version):
        return """#!/bin/bash

# GENERATED DURING INSTALLATION VARS
INSTALLED_PATH=\"""" + install_path + """\"
VERSION=""" + version + """

# COMMON VARS
COMMON_PATH_TO_BINARY="Authoring/x64/Release/bin"
COMMON_PATH_TO_BINARY_WIN="`echo $COMMON_PATH_TO_BINARY | sed -e 's:/:\\\\\\\\:g'`"
EXEC_NAME="Wwise.exe"

EXECUTE="${INSTALLED_PATH}/Wwise ${VERSION}/${COMMON_PATH_TO_BINARY}/${EXEC_NAME}"

export WWISEROOT="`winepath -w \\"${INSTALLED_PATH}/Wwise ${VERSION}\\"`"
export WWISESDK="${WWISEROOT}\SDK"
export WWISE_EXE_PATH="${WWISEROOT}"\\\\"${COMMON_PATH_TO_BINARY_WIN}"
export WWISE_COMMON_GENERATEDSOUNDBANKS_PATH="GeneratedSoundBanks"
export WINEDEBUG=-all

exec wine "${EXECUTE}"
"""

    @staticmethod
    def _get_json_launcher_info():
        return {
            "version": {
                "year": FakeLauncher.version["year"],
                "major": FakeLauncher.version["major"],
                "minor": str(FakeLauncher.version["minor"]),
                "build": FakeLauncher.version["build"]
            },
            "platform": FakeLauncher.platform
        }

    @staticmethod
    def _get_context():
        return {
            "version": 1
        }
    
    @staticmethod
    def _get_post_data_for_post_requests():
        return json.dumps({
            "jwt": FakeLauncher.jwt,
            "context": FakeLauncher._get_context(),
            "launcher": FakeLauncher._get_json_launcher_info(),
            "launcherInfo": FakeLauncher._get_json_launcher_info()
        })

    @staticmethod
    def get_payload_and_verify_signature(response):
        # TODO: verify signature
        return base64.b64decode(json.loads(response)["payload"],)

    @staticmethod
    def login_as(email, password):
        dl_process = Downloader.POST("email=" + email + "&password=" + password, "https://www.audiokinetic.com/wwise/launcher/?action=login", wget_stdout = subprocess.PIPE)

        response = ""
        for out in dl_process.get_output():
            response += out

        dl_process.wait_finish()

        payload = FakeLauncher.get_payload_and_verify_signature(response)

        # TODO: check signature
        FakeLauncher.jwt = json.loads(payload)["jwt"]
        FakeLauncher.save_jwt_to_file()

    @staticmethod
    def update_login_u_id():
        try:
            # base64.b64decode does not include automatically the padding but it does ignore the extras
            # Melius abundare quam deficere
            jwt_body = json.loads(base64.b64decode(FakeLauncher.jwt.split(".")[1].encode('utf-8')  + b"========"))["u_id"]
        except Exception as e:
            print(e)
            print("Couldn't read the \"u_id\" from jwt.")
            FakeLauncher.u_id = ""
        else:
            FakeLauncher.u_id = jwt_body
            print("Logged in as '" + FakeLauncher.u_id + "'.")


    @staticmethod
    def load_jwt_from_file():
        with open(FakeLauncher.jwt_location, "r") as f:
            FakeLauncher.jwt = f.read().replace("\n", "").replace("\r", "")

    @staticmethod
    def save_jwt_to_file():
        with open(FakeLauncher.jwt_location, "w") as f:
            f.write(FakeLauncher.jwt)

    @staticmethod
    def login_as_guest():
        FakeLauncher.login_as("", "")
    
    @staticmethod
    def logout():
        FakeLauncher.login_as_guest()
    
    @staticmethod
    def download_file(file, destination_dir = ".", url = "", force = False):
        if os.path.exists(destination_dir + "/" + file["id"]) and\
           subprocess.check_output([ "sha1sum", destination_dir + "/" + file["id"] ]).decode('utf-8').split(" ")[0] == file["sha1"] and not force:
           return

        header = [ "Content-type: application/json", "Authorization: Bearer " + FakeLauncher.jwt ]
        if "method" in file and file["method"] == "POST":
            return Downloader.POST(
                FakeLauncher._get_post_data_for_post_requests(),
                file["url"] if "url" in file else url,
                file["id"],
                destination_dir,
                headers=header,
                wget_stdout=sys.stdout
            )
        else:
            return Downloader.GET(
                file["url"] if "url" in file else url,
                output=file["id"],
                destination=destination_dir,
                headers=header,
                wget_stdout=sys.stdout
            )

    @staticmethod
    def download_bundle(bundle, url = ""):
        id = bundle if isinstance(bundle, str) else bundle["id"]
        dl_process = Downloader.GET(
            "https://blob-api.gowwise.com/products/versions/" + id,
            headers=[ "Content-type: application/json", "Authorization: Bearer " + FakeLauncher.jwt ],
            wget_stdout=subprocess.PIPE
        )
        
        response = ""
        for out in dl_process.get_output():
            response += out

        dl_process.wait_finish()

        b = FakeLauncher.get_payload_and_verify_signature(response)

        with open(FakeLauncher.bundles_dir + "/" + id + ".json", "w") as file:
            bundle = json.loads(b.decode('utf-8'))["data"]
            file.write(json.dumps(bundle))
            file.close()
        
        return bundle

    @staticmethod
    def update_bundles():
        for category in BundleType.get_all():
            dl_process = Downloader.GET(
                "https://blob-api.gowwise.com/products/versions/?category=" + category,
                headers=[ "Content-type: application/json", "Authorization: Bearer " + FakeLauncher.jwt ],
                wget_stdout=subprocess.PIPE
            )

            response = ""
            for out in dl_process.get_output():
                response += out

            dl_process.wait_finish()

            b = FakeLauncher.get_payload_and_verify_signature(response)

            with open(FakeLauncher.bundles_dir + "/" + category + ".json", "w") as file:
                bundle = json.loads(b.decode('utf-8'))["data"]
                file.write(json.dumps(bundle))
                file.close()

        return FakeLauncher.bundles

    @staticmethod
    def load_bundles_from_file():
        for category in BundleType.get_all():
            with open(FakeLauncher.bundles_dir + "/" + category + ".json", "r") as file:
                FakeLauncher.bundles[category] = json.loads(file.read())["bundles"]

    @staticmethod
    def get_bundle_by_id(bundle_id):
        for category in BundleType.get_all():
            try:
                if not FakeLauncherSettings.is_debug(): raise Exception
                with open(FakeLauncher.bundles_dir + "/" + bundle_id + ".json") as f:
                    return json.loads(f.read())
            except:
                for b in FakeLauncher.bundles[category]:
                    if "id" in b and b["id"] == bundle_id:
                        return FakeLauncher.download_bundle(b)
                # return FakeLauncher.download_bundle(bundle_id)
        return None
    
    @staticmethod
    def _are_same_version(version1, version2):
        if version2 is None: return False
        for k in version2.keys():
            if k == "nickname": continue
            if not (k in version1): return False
            if version1[k] != version2[k]: return False
        return True

    @staticmethod
    def get_version_as_string(bundle):
        if "version" in bundle:
            return str(bundle["version"]["year"]) + "." + str(bundle["version"]["major"]) + "." + str(bundle["version"]["minor"]) + "." + str(bundle["version"]["build"])
        return "no version"

    @staticmethod
    def _is_bundle_targeting_this_version(bundle, version):
        if bundle["type"] == BundleType.sample:
            if FakeLauncher._are_same_version(version, bundle["version"]): return True
            if "productDependentData" in bundle and "targetWwiseVersion" in bundle["productDependentData"]:
                wwise_version_target = bundle["productDependentData"]["targetWwiseVersion"]
                for k in wwise_version_target.keys():
                    if not (k in version): return False
                    if version[k] != wwise_version_target[k]: return False
                return True
        else:
            return FakeLauncher._are_same_version(version, bundle["version"])

    @staticmethod
    def get_all_bundles_of_type(bundle_type):
        return FakeLauncher.bundles[bundle_type]
        # array = []
        # for b in FakeLauncher.bundles:
        #     if "type" in b and b["type"] == bundle_type:
        #         array.append(b)
        # return array

    @staticmethod
    def _file_is_in_list(l, file_id, file_display_name = None):
        # TODO: maybe there is a better way to ignore older packages but for now no "version"-like field is present in the bundles
        for f in l:
            if ("id" in f and f["id"] == file_id) or ((not (file_display_name is None)) and (("displayName" in f and f["displayName"] == file_display_name) or ("name" in f and f["name"] == file_display_name))): return True
        return False

    @staticmethod
    def get_all_available_bundles_for_wwise_version(wwise_version_object, bundle_type = None):
        array = []
        for p in FakeLauncher.get_bundle_by_id("wwise." + str(wwise_version_object["year"]) + "_" + str(wwise_version_object["major"]) + "_" + str(wwise_version_object["minor"]) + "_" + str(wwise_version_object["build"]))["children"]:
            name = p["name"] if "name" in p else (p["displayName"] if "displayName" in p else None)
            if (bundle_type is None or ("type" in p and p["type"] == bundle_type)) and (not FakeLauncher._file_is_in_list(array, p["id"], name)):
                array.append(p)
        return array

    @staticmethod
    def get_all_bundles_for_wwise_version(wwise_version_object, bundle_type = None):
        array = []
        for p in FakeLauncher.get_bundle_by_id("wwise." + str(wwise_version_object["year"]) + "_" + str(wwise_version_object["major"]) + "_" + str(wwise_version_object["minor"]) + "_" + str(wwise_version_object["build"]))["children"]:
            name = p["name"] if "name" in p else (p["displayName"] if "displayName" in p else None)
            if (bundle_type is None or ("type" in p and p["type"] == bundle_type)) and (not FakeLauncher._file_is_in_list(array, p["id"], name)):
                array.append(FakeLauncher.get_bundle_by_id(p["id"]))
        return array

    @staticmethod
    def get_all_files_for_version(from_bundle_of_type, version_object, bundle_type = None):
        array = []
        for p in FakeLauncher.get_bundle_by_id(from_bundle_of_type.lower() + "." + str(version_object["year"]) + "_" + str(version_object["major"]) + "_" + str(version_object["minor"]) + "_" + str(version_object["build"]))["files"]:
            name = p["name"] if "name" in p else (p["displayName"] if "displayName" in p else None)
            if (bundle_type is None or ("type" in p and p["type"] == bundle_type)) and (not FakeLauncher._file_is_in_list(array, p["id"], name)):
                array.append(FakeLauncher.get_bundle_by_id(p["id"]))
        return array


    @staticmethod
    def update_wwise_launcher_infos():
        dl_process = Downloader.GET(
            "https://blob-api.gowwise.com/products/versions/?category=" + BundleType.launcher,
            headers=[ "Content-type: application/json", "Authorization: Bearer " + FakeLauncher.jwt ],
            wget_stdout=subprocess.PIPE
        )

        response = ""
        for out in dl_process.get_output():
            response += out

        dl_process.wait_finish()

        b = FakeLauncher.get_payload_and_verify_signature(response)

        with open(FakeLauncher.config_dir + "/wwise_launcher_version.txt", "w") as file:
            bundle = json.loads(b.decode('utf-8'))["data"]["bundles"][0]
            FakeLauncher.most_recent_launcher = bundle
            FakeLauncher.version = FakeLauncher.most_recent_launcher["version"]
            file.write(json.dumps(bundle))
            file.close()

        return bundle

    @staticmethod
    def load_wwise_launcher_info():
        try:
            f = open(FakeLauncher.config_dir + "/wwise_launcher_version.txt", "r")
            FakeLauncher.version = json.loads(f.read())["version"]
        except:
            print("Couldn't load wwise launcher version from file")

    @staticmethod
    def get_values_in_group(bundle, group_id):
        if not ("groups" in bundle):
            return None

        for group in bundle["groups"]:
            if "id" in group and group["id"] == group_id:
                if group is None or not ("values" in group):
                    return None
                
                return group["values"]

        return None

    @staticmethod
    def get_files_in_bundle(bundle):
        if "files" in bundle: return bundle["files"]
        return None

    @staticmethod
    def is_value_visible(value):
        return "$visible" in value and isinstance(value["$visible"], bool) and value["$visible"]

    @staticmethod
    def is_value_checked(value):
        return "$checked" in value and isinstance(value["$checked"], bool) and value["$checked"]

    @staticmethod
    def get_value_description(value):
        return "" if not ("description" in value) else str(value["description"].replace(". ", ".\n"))

    @staticmethod
    def get_value_id(value):
        return "" if not ("id" in value) else str(value["id"])

    @staticmethod
    def get_value_display_name(value):
        return "" if not ("displayName" in value) else str(value["displayName"])

    @staticmethod
    def get_value_name(value):
        return "" if not ("name" in value) else str(value["name"])

    @staticmethod
    def get_value_labels(value):
        array = []
        if "labels" in value and isinstance(value["labels"], list) and len(value["labels"]) > 0:
            for i in range(len(value["labels"])):
                if "displayName" in value["labels"][i]:
                    array.append(str(value["labels"][i]["displayName"]))
        return array

    @staticmethod
    def get_value_labels_as_string(value):
        label_string = ""
        i = 0
        labels = FakeLauncher.get_value_labels(value)
        for l in labels:
            if i == len(labels) - 1:
                label_string += str(l)
            else:
                label_string += str(l) + ", "
            i += 1
        return label_string

    @staticmethod
    def is_file_downloadable(file):
        return (("url" in file) and (len(file["url"]) > 0))

    @staticmethod
    def extract_archive(archive_path, dest_path = ".", skip_old_files = True):
        command = [ "tar", "xf", archive_path, "--directory", dest_path ]
        if skip_old_files:
            command.append("--skip-old-files")
        return subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)

    @staticmethod
    def _init_mk_config_dir():
        # Silently create config directory
        try:
            os.makedirs(FakeLauncher.config_dir)
        except:
            pass

        try:
            os.makedirs(FakeLauncher.bundles_dir)
        except:
            pass

    @staticmethod
    def _init_jwt():
        # Load JWT or get a new one
        try:
            FakeLauncher.load_jwt_from_file()
        except:
            print("JWT file not found: logging in as guest")
            try:
                FakeLauncher.login_as_guest()
            except:
                print("Couldn't download a JWT file: check your internet connection.")
        else:
            FakeLauncher.load_jwt_from_file()
            FakeLauncher.update_login_u_id()
            print("Loaded JWT file.")

    @staticmethod
    def _init_bundles():
        if FakeLauncherSettings.is_debug():
            try:
                FakeLauncher.load_bundles_from_file()
            except:
                FakeLauncher.update_bundles()
                FakeLauncher.load_bundles_from_file()
        else:
            try:
                FakeLauncher.update_bundles()
            except:
                print("Couldn't update bundles.json file: check your internet connection.")
                FakeLauncher.login_as_guest()
            finally:
                try:
                    FakeLauncher.load_bundles_from_file()
                except:
                    print("Couldn't load the file bundles.json. Aborting.")
                    quit(1)
                else:
                    print("Bundle loaded correctly.")

    @staticmethod
    def save_bundle_to_file(file_path, bundle_id):
        bundle = FakeLauncher.get_bundle_by_id(bundle_id)
        with open(file_path, "w+") as file:
            file.write(json.dumps(bundle))
            file.close()

    @staticmethod
    def init_install_entry(bundle_id):
        return dict(FakeLauncher.get_bundle_by_id(bundle_id))

    @staticmethod
    def init():
        FakeLauncher._init_mk_config_dir()
        FakeLauncher._init_jwt()
        FakeLauncher.load_wwise_launcher_info()
        FakeLauncher._init_bundles()
        FakeLauncher.update_wwise_launcher_infos()

    @staticmethod
    def is_valid_unity_project_directory(path):
        return os.path.isdir(path + "/Assets") and \
               os.path.isdir(path + "/Packages") and \
               os.path.isdir(path + "/ProjectSettings") and \
               os.path.isfile(path + "/ProjectSettings/ProjectSettings.asset") and \
               os.path.isfile(path + "/ProjectSettings/ProjectVersion.txt")

    @staticmethod
    def get_unity_project_version(path):
        if not FakeLauncher.is_valid_unity_project_directory(path):
            return ""
        
        with open(path + "/ProjectSettings/ProjectVersion.txt") as p_ver:
            loaded = yaml.load(p_ver, Loader=yaml.FullLoader)
            return loaded["m_EditorVersion"]

    @staticmethod
    def unity_project_has_wwise_integration(path):
        if not FakeLauncher.is_valid_unity_project_directory(path):
            return False

        return os.path.isfile(path + "/Assets/Wwise/Version.txt") or os.path.isfile(path + "/Assets/Wwise/NewVersion.txt")

    @staticmethod
    def get_unity_project_wwise_integration_version(path):
        if not FakeLauncher.unity_project_has_wwise_integration(path):
            return 0

        version_file_path = ""
        if os.path.isfile(path + "/Assets/Wwise/Version.txt"):
            version_file_path = path + "/Assets/Wwise/Version.txt"
        else:
            version_file_path = path + "/Assets/Wwise/NewVersion.txt"

        with open(version_file_path) as version_file:
            for l in version_file.readlines():
                if "Unity Integration Version:" in l:
                    return int(l.split(":")[1].strip())
        return 0

    @staticmethod
    def get_unity_editor_install_location_from_unityhub():
        with open(os.environ.get("HOME") + "/.config/UnityHub" + "/secondaryInstallPath.json") as unity_editor_path_file:
            return unity_editor_path_file.readline().strip().strip("\"").rstrip("/")

    @staticmethod
    def get_unity_editor_executable(version):
        install_path = FakeLauncher.get_unity_editor_install_location_from_unityhub()
        return install_path + "/" + version + "/Editor/Unity"

    @staticmethod
    def apply_unity_integration_patch(project_path):
        if not FakeLauncher.unity_project_has_wwise_integration(project_path):
            raise FakeLauncherException("This project has no Wwise Integration installed.")

        unity_integration_version = FakeLauncher.get_unity_project_wwise_integration_version(project_path)

        if not unity_integration_version in supported_unity_integration_versions:
            raise FakeLauncherException("Unity Integration Version " + str(unity_integration_version) + " not supported.")

        convert_all_CRLF_to_LF(project_path, "cs")

        return apply_patch(project_path, FakeLauncher.get_unity_integration_patch_path(unity_integration_version))

    @staticmethod
    def get_unity_integration_patch_path(version):
        return FakeLauncher.wwiser_launcher_location + "/unity_integration/patches/patch_v" + str(version) + ".patch"

    @staticmethod
    def install_wine_helper_in_project(project_path):
        if not FakeLauncher.unity_project_has_wwise_integration(project_path):
            raise FakeLauncherException("This project has no Wwise Integration installed.")
        
        unity_integration_version = FakeLauncher.get_unity_project_wwise_integration_version(project_path)

        relative_destination = project_path
        if unity_integration_version <= 18:
            relative_destination = project_path + "/Assets"
        else:
            relative_destination = project_path + "/Assets/Wwise/API/Runtime"
        
        return subprocess.Popen([ "cp", FakeLauncher.wwiser_launcher_location + "/unity_integration/WineHelper.cs", relative_destination ], stdout=subprocess.PIPE, universal_newlines=True)

def apply_patch(destination_directory, path_to_patch, backup_originals = False):
    command = [ "patch", "-u" ]
    if backup_originals:
        command.append([ "-b" ])
    command += [ "-d", destination_directory, "-p0" ]

    with open(path_to_patch) as patch_file:
        return subprocess.Popen(command, stdin=patch_file, stdout=subprocess.PIPE, universal_newlines=True)

def convert_all_CRLF_to_LF(directory = ".", extension = "*"):
    # No seriously, whats wrong with people using CRLF?
    for (i, file) in enumerate(recursively_list_all_files_in_dir(directory, extension)):
        subprocess.call([ "sed", "-i", "s/\\r$//g", str(file) ])

def recursively_list_all_files_in_dir(directory = ".", extension = "*"):
    return list(pathlib.Path(directory).rglob("*." + extension))