#!/bin/bash

BUILD=
MAJOR=
MINOR=
YEAR=
WWISE=

get_wwise_version() {
    test ! -f ./bundle/install-entry.json && echo "bundle/install-entry.json file not found. Aborting." >&2 && exit 1

    JSON=`cat ./bundle/install-entry.json | grep \"bundle\" -A 11 | grep \"version\" -A15 | sed '/}/q'`
    BUILD=`echo "$JSON" | grep build | sed -e 's/[^0-9]//g'`
    MAJOR=`echo "$JSON" | grep major | sed -e 's/[^0-9]//g'`
    MINOR=`echo "$JSON" | grep minor | sed -e 's/[^0-9]//g'`
    YEAR=`echo "$JSON" | grep year | sed -e 's/[^0-9]//g'`

    WWISE="Wwise $YEAR.$MAJOR.$MINOR.$BUILD"
    echo "Started offline installation of $WWISE"
}

default_install_path() {
    INSTALL_PATH="${HOME}/.wine/drive_c/Program Files (x86)/Audiokinetic/${WWISE}"
    echo "Installing in ${INSTALL_PATH}..."
    mkdir -p "${INSTALL_PATH}"
}

ask_export_variables() {
    echo -en "Automatically export Wwise variables?\nThis action will modify your ~/.bashrc.\n(not recommended if you have multiple installation of wwise)\n[y/N]: "
    read ANSWER
    if [[ "$ANSWER" =~ ^[yYsS] ]]; then
        # export WWISEROOT variable
        test `cat ${HOME}/.bashrc | egrep "^export WWISEROOT=" | wc -l` -eq 0 \
            && echo "export WWISEROOT=\"${INSTALL_PATH}\"" >> ${HOME}/.bashrc \
            || sed -i 's:^export WWISEROOT=.*$:export WWISEROOT='"\"${INSTALL_PATH}\""':' ${HOME}/.bashrc

        # export WWISESDK variable
        test `cat ${HOME}/.bashrc | egrep "^export WWISESDK=" | wc -l` -eq 0 \
            && echo "export WWISESDK=\"\${WWISEROOT}/SDK\"" >> ${HOME}/.bashrc \
            || sed -i 's:^export WWISESDK=.*$:export WWISESDK='"\"\${WWISEROOT}/SDK\""':' ${HOME}/.bashrc
    fi
}

install_archives() {
    local ERRORS=0
    for archive in `ls -1 ./bundle/*.tar.xz`
    do
        echo -n "Extracting ${archive}... "
        # --skip-old-files option is justified because you may want to add plugins and the current files will
        # never change in the context of the same Wwise version
        tar xf "${archive}" --directory "${INSTALL_PATH}" --skip-old-files
        test "$?" -eq 0 && echo "done" || (echo "FAIL" && ERRORS=$(($ERRORS + 1)))
    done
    echo "Installation exited with ${ERRORS} errors."
}

find_problematic_case_sensitive_directories() {
    local ERRORS=0
    local MOVED_DIRS=0

    PROBLEMATIC_DIRS="`find \"${INSTALL_PATH}\" -type d | sort -f | uniq -id`"

    test -z "${PROBLEMATIC_DIRS}" && return 0

    echo "WARNING!!!"
    echo "Problematic dirs were found in install path."
    echo
    echo "This is a problem based on the different sensitivity of *nix and"
    echo "Windows filesystems."
    echo "Having in the wine configuration directory directories with the same"
    echo "name but different uppercase and lowercase may lead to really difficult"
    echo "to diagnose problems."
    echo
    echo "The following section will guide you solving these conflicts."
    echo
    echo "It is a good idea to always keep the \"all lowercase\" directory."

    local SAVEIFS=$IFS
    IFS=$(echo -en "\n\b")

    for d in `echo "${PROBLEMATIC_DIRS}"`; do
        echo
        IFS=$SAVEIFS

        local OCCURRED="`find \"${INSTALL_PATH}\" -iwholename \"${d}\" -type d`"

        IFS=$(echo -en "\n\b")

        PS3="Which one do you want to keep for \"$d\"? "

        local CASES=
        for o in `echo "${OCCURRED}"`; do CASES="$CASES\"$o\":"; done

        IFS=$(echo -en ":")
        local ARRAY=(${CASES%:})
        IFS=$(echo -en "\n\b")

        select _ in "${ARRAY[@]}"; do
            if [ $REPLY -ge 1 ] && [ $REPLY -le ${#ARRAY[@]} ]; then
                echo "Selected ${ARRAY[$(($REPLY - 1))]}"

                local DEST="`echo ${ARRAY[$(($REPLY - 1))]} | sed -e 's/^"//' | sed -e 's/"$//'`"

                for a in "${ARRAY[@]}"; do
                    local SRC="`echo ${a} | sed -e 's/^"//' | sed -e 's/"$//'`"
                    test "$SRC" == "$DEST" && continue

                    MOVED_DIRS=$(($MOVED_DIRS+1))

                    IFS=$SAVEIFS
                    mv -f "$SRC"/* "$DEST"
                    rmdir "$SRC" > /dev/null 2>&1 || (echo "ERROR: Unable to remove directory ${SRC}. This is going to be a problem!!!" && ERRORS=$(($ERRORS + 1)))
                    IFS=$(echo -en "\n\b")

                done

                break
            fi
        done

    done

    echo "Solved problematic directories path with ${ERRORS} errors."

    if [ $MOVED_DIRS -gt 0 ]; then
        # need to be recurisve to fix possibles problematic directories after moves
        find_problematic_case_sensitive_directories
    fi

    IFS=$SAVEIFS
}

_find_writable_path() {
    INSTALL_LAUNCH_SCRIPT_IN=
    local WRITABLE_PATHS=`for path in $(echo $PATH | sed -e 's/:/\n/g'); do test -d "$path" && test -w "$path" && echo "\"$path\""; done`
    local ARRAY=($(echo ${WRITABLE_PATHS%:}:\"${HOME}\" | sed -e 's/:/ /g'))

    PS3="Where do you want to install \"wwise_${WWISE#Wwise }\" script to launch authoring app? "

    select _ in "${ARRAY[@]}"; do
        if [ $REPLY -ge 1 ] && [ $REPLY -le ${#ARRAY[@]} ]; then
            INSTALL_LAUNCH_SCRIPT_IN="${ARRAY[$(($REPLY - 1))]}"
            break
        fi
    done

    test -z "${INSTALL_LAUNCH_SCRIPT_IN}" && test -w "${HOME}" && INSTALL_LAUNCH_SCRIPT_IN="${HOME}"
}

generate_wwise_authoring_launch_script() {
    _find_writable_path

    if [ -z "${INSTALL_LAUNCH_SCRIPT_IN}" ]; then
        echo
        echo "No writable path found. The script to execute Wwise Authroing app will be printed in stdout."
        echo "Please, copy-paste it in a file before it get lost in space and time."
        echo
        echo "BTW: this messages is the result of your HOME not being writable. You may have bigger problems"
        echo "than not being able to run Wwise Authoring app."
        echo
        echo "##################################################################################"
        echo "#                               SCRIPT BEGINNING                                 #"
        echo "##################################################################################"
        cat ./wwise_authoring_script \
            | sed -e 's:^INSTALLED_PATH=$:INSTALLED_PATH=\"'"${INSTALL_PATH%/${WWISE}}"'\":' \
            | sed -e 's:^VERSION=$:VERSION=\"'"${WWISE#Wwise }"'\":'
        echo "##################################################################################"
        echo "#                                  SCRIPT END                                    #"
        echo "##################################################################################"
    else
        echo "Installing wwise_${WWISE#Wwise } in ${INSTALL_LAUNCH_SCRIPT_IN}"
        cat ./wwise_authoring_script \
            | sed -e 's:^INSTALLED_PATH=$:INSTALLED_PATH=\"'"${INSTALL_PATH%/${WWISE}}"'\":' \
            | sed -e 's:^VERSION=$:VERSION=\"'"${WWISE#Wwise }"'\":' > "${INSTALL_LAUNCH_SCRIPT_IN}/wwise_${WWISE#Wwise }"
        chmod +x "${INSTALL_LAUNCH_SCRIPT_IN}/wwise_${WWISE#Wwise }"
    fi
}

get_wwise_version
default_install_path
install_archives
find_problematic_case_sensitive_directories
ask_export_variables
generate_wwise_authoring_launch_script