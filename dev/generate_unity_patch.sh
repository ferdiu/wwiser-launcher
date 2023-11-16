#!/bin/bash

set -e

# variables
UNITY_VERSION=2022.3.1f1

# definitions
UNITY_EXE="/opt/unity-editor/${UNITY_VERSION}/Editor/Unity"
PROJ_DIR=unity_project

# create unity project
"$UNITY_EXE" -createProject "$PROJ_DIR" -logFile "${PROJ_DIR}.log" -batchmode -quit
wget "https://raw.githubusercontent.com/github/gitignore/main/Unity.gitignore" -O "$PROJ_DIR/.gitignore"
{
    echo "**.rej"
    echo "**.orig"
    echo "**.rej.meta"
    echo "**.orig.meta"
} >> "$PROJ_DIR/.gitignore"

# start procedure
cd "$PROJ_DIR"
git init

git add .
git commit -m "vanilla"
echo "Start the \`wwiser-launcher.py\` script, make sure you turned on the developer mode"
echo "and the start follow the procedure \`Apply Unity Integration\`. When asked for the"
echo "project directory select the directory:"
echo -e -n "\t"
realpath .
echo ""
echo -n "Press [ENTER] to continue"
read -r

git add .
git commit -m "wwise integration"
echo -n "Now go back to the \`wwiser-launcher.py\` process and follow the procedure."
echo ""
echo -n "Press [ENTER] to continue"
read -r

git add .
git commit -m "wwise integration patch"

git format-patch HEAD^..HEAD --stdout > ../generated.patch
echo "Generated patch at $(realpath ../generated.patch)"

cd -
