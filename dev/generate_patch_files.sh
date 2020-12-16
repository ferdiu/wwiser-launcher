#!/bin/bash

ORIGINAL="${1%/}"
PATCHED="${2%/}"

usage() {
    echo "Usage: $0 [ORIGINAL PROJECT DIR] [PATCHED PROJECT DIR]" >&2
    exit 1
}

if [ -z "$1" ] || [ -z "$2" ]; then
    usage
fi

FILES=("Assets/Wwise/Deployment/API/Handwritten/Common/AkUtilities.cs" \
"Assets/Wwise/Deployment/API/Handwritten/Common/AkCommonPlatformSettings.cs" \
"Assets/Wwise/Deployment/API/Handwritten/Common/AkBasePathGetter.cs" \
"Assets/Wwise/Editor/WwiseWindows/AkWwisePicker.cs" \
"Assets/Wwise/Editor/WwiseSetupWizard/AkPluginActivator.cs")

OUT_DIR=./generated_patches

for f in "${FILES[@]}"; do
    LC_ALL=C TZ=UTC0 diff -u "${ORIGINAL}/${f}" "${PATCHED}/${f}" > "${OUT_DIR}/${f##*/}.patch"
    sed -i 's:'"${ORIGINAL}"'/::' "${OUT_DIR}/${f##*/}.patch"
    sed -i 's:'"${PATCHED}"'/::' "${OUT_DIR}/${f##*/}.patch"
done

mv -f generated_patches/*.patch ../unity_integration/patches
