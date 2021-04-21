# TODO

## General

- Implement ui.console.py and ui.kdialog.py
- Show Download progress in Zenity (and console and kdialog in the future)
- Handle login
- Unreal Integration
- Godot Integration
- Downloader should be able to use curl if wget is not installed

## Installation

- Generate install-entry.json during installation procedure
- Add step for extraction

## Unity Integration

- Automatically change to winepath-like the value of WwiseInstallationPathWindows in WwiseSettings.xml
- Automatically link GeneratedSoundBanks directory in wwise project to the Unity Project directory in StreamingAssets and remove "extra steps" from Wwise Project Settings (which cause errors when generating soundbanks)
