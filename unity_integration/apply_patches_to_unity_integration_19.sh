#!/bin/bash

UNITY_INTEGRATION_VERSION=19
PATCHES_DIR="${WWISER_LAUNCHER_DIR}/unity_integration/patches_v${UNITY_INTEGRATION_VERSION}"
WINE_HELPER_DIR="${WWISER_LAUNCHER_DIR}/unity_integration"

if [ -z "${PROJECT_PATH}" ]; then
    echo "No PROJECT_PATH variable set, exiting." >&2
    exit 1
fi

PROJECT_PATH="${PROJECT_PATH%/}"

BACKUP_ORIGINALS="-b"

if [ -n "${BACKUP_NOT_NEEDED}" ]; then
    BACKUP_ORIGINALS=
fi

patch_wrongly_generated_cs_files() {
    local SAVEIFS=$IFS
    IFS=$(echo -en "\n\b")

    for f in ${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/*.cs; do
        IFS=$SAVEIFS

        sed -i 's/^#if UNITY_STANDALONE_LINUX \&\& \! UNITY_EDITOR$/#if (UNITY_STANDALONE_LINUX \&\& \! UNITY_EDITOR) \|\| UNITY_EDITOR_LINUX/g' "$f"

        IFS=$(echo -en "\n\b")
    done

    IFS=$SAVEIFS
}

patch_files_in_AkCommon_dir() {
    patch -u ${BACKUP_ORIGINALS} -d "${PROJECT_PATH}" -p0 < "${PATCHES_DIR}/AkUtilities.cs.patch"
    patch -u ${BACKUP_ORIGINALS} -d "${PROJECT_PATH}" -p0 < "${PATCHES_DIR}/AkCommonPlatformSettings.cs.patch"
    patch -u ${BACKUP_ORIGINALS} -d "${PROJECT_PATH}" -p0 < "${PATCHES_DIR}/AkBasePathGetter.cs.patch"
}

patch_AkWwisePicker() {
    patch -u ${BACKUP_ORIGINALS} -d "${PROJECT_PATH}" -p0 < "${PATCHES_DIR}/AkWwisePicker.cs.patch"
}

patch_AkPluginActivator() {
    patch -u ${BACKUP_ORIGINALS} -d "${PROJECT_PATH}" -p0 < "${PATCHES_DIR}/AkPluginActivator.cs.patch"
}

install_WineHelper() {
    cp -v "${WINE_HELPER_DIR}/WineHelper.cs" "${PROJECT_PATH}/Assets/"
}

wwise_files_are_present() {
    return \
        $(test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Handwritten/Common/AkUtilities.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Handwritten/Common/AkCommonPlatformSettings.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Handwritten/Common/AkBasePathGetter.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Editor/WwiseWindows/AkWwisePicker.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Editor/WwiseSetupWizard/AkPluginActivator.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkAudioAPI_Linux.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkCommunicationSettings_Linux.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkMemPoolAttributes_Linux.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkPlatformInitSettings_Linux.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEngine_Linux.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEnginePINVOKE_Linux.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkThreadProperties_Linux.cs" && \
        test -f "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkUnityPlatformSpecificSettings_Linux.cs"; echo $?)
}

convert_CRLF_to_LF() {
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Handwritten/Common/AkUtilities.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Handwritten/Common/AkCommonPlatformSettings.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Handwritten/Common/AkBasePathGetter.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Editor/WwiseWindows/AkWwisePicker.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Editor/WwiseSetupWizard/AkPluginActivator.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkAudioAPI_Linux.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkCommunicationSettings_Linux.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkMemPoolAttributes_Linux.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkPlatformInitSettings_Linux.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEngine_Linux.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEnginePINVOKE_Linux.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkThreadProperties_Linux.cs"
    sed -i 's/\r$//g' "${PROJECT_PATH}/Assets/Wwise/Deployment/API/Generated/Linux/AkUnityPlatformSpecificSettings_Linux.cs"
}

if ! wwise_files_are_present; then
    echo "Not all the files that need to be patched are present in this project. Aborting." >&2
    exit 1
fi

install_WineHelper
convert_CRLF_to_LF
patch_files_in_AkCommon_dir
patch_AkWwisePicker
patch_AkPluginActivator
patch_wrongly_generated_cs_files
