# wWiserLauncher

Wwiser Launcher is a set of bash scripts for Linux which aims to replace the Wwise Launcher (Mac and Windows only).

### Disclaimer

This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by Audiokinetic nor Unity Technologies. All product and company names are the registered trademarks of their original owners. The use of any trade name or trademark is for identification and reference purposes only and does not imply any association with the trademark holder of their product brand.

While the informations and scripts in this project have been verified to the best of my abilities, I can't guarantee that there are no mistakes or errors. If you find any, please report it.

### Advice

Use a version-control system (as `git`) ad commit all your work before applying the Unity Integration Patch.

## Usage

Currently this is under development. I'm planning to make this process automated in the near future but, for now, you still need the Wwise Launcher installed with wine.

### Install Wwise Authroing Application

The flow to have the Authoring application working is currently this:

- Install [Wwise Launcher](https://www.audiokinetic.com/downloads/#windows) for Windows with Wine (`wine msiexec /i [PATH TO INSTALLER]/WwiseLauncher.msi`)
- Use the Launcher[\*](#first-warn) to prepare an offline installation [selecting all the needed softwares and plugins](https://www.audiokinetic.com/library/edge/?source=InstallGuide&id=installing_or_upgrading_wwise_and_its_packages#to_install_wwise)
- Use the terminal to browse to the location where you generated the offline installer
- Execute the `install_wwise.sh` script inside the proper directory[\*\*](#second-warn)
- Wait until the process ends (DO NOT IGNORE ERRORS) and, if any, answer the questions
- Do not forget to set the compatibility mode for Windows XP* in `winecfg` for `[INSTALLED_PATH]/Authoring/x64/Release/bin/Wwise.exe` file
- If the installer script found a writable path to install the `wwise_YEAR.MAJOR.MINOR.BUILD` script in your `PATH` variable all you need to do is execute in a terminal `wwise_YEAR.MAJOR.MINOR.BUILD` replacing the appropriate fields (ex: `wwise_2019.1.10.7250`) or just letting the auto-completion do its magic
- If the installer couldn't find any writable path in your `PATH` variable you will find the script inside your `HOME`

<a name="first-warn">\*</a> Wwise Launcher and Wwise Authoring application need to be launched with compatibility for Windows XP [run `winecfg` and go to `Application` tab > Under `Application settings` > `Add application` > select your `Wwise Launcher.exe` > Pick `Windows version` > `Windows XP` ] otherwise you will see a black screen (this is a well known problem with [Electron](https://www.electronjs.org/) apps in wine) and the Authoring app will load your project endlessly. 

<a name="second-warn">\*\*</a> if you see error as `bundle/install-entry.json file not found. Aborting.` then you are probably in the wrong directory; you have to execute it in the directory containing `bundle/` dir and `WwiseLauncher.msi` file.

### Apply Unity Integration Patch

Unity Integration patch assumes that you installed the Wwise Authoring application in your wine directory. Most of this work is done with this in mind.

** Currently under development **

For now the only way to make this work is to integrate Wwise in your project using Mac or Windows and then apply the patch as described.

This limitation is due to the fact that the downloader is still under development (it can barely download the jwt needed to authenticate with guest login at this moment).

For an explaination of what the patches do see this [text file](unity_integration/patches/README.txt).

## Dependencies and Requirements

No root permission is needed.

The scripts are currently tested under Debian 10 GNU/Linux (Linux kernel 4.19.0) with Wine Staging (v6.0-rc1).

- Wine Staging (v6.0-rc1 or above)
- make sure to have in your `PATH` the `winepath` util to convert path between unix and wine paths

Used inside scripts

- `tar` (for archives extraction during installation)
- `sed` (currently tested only with the GNU version but there is no reason to think it would not work with the standard version)

The downloader (which currently does not work) needs:

- `base64` (needed by the download)
- `wget` (planning to support `curl` too as an alternative)

## Contribute

### Installer

Any bug report is helpful and any feature request is welcomed.

### Unity Integration

Since Wwise is running on Wine on Mac too, most of the work done in the C# scripts of the Wwise Unity Integration was made mimicking the decisions took for this platform and adapting it for the Linux + Wine configuration.

Everything in the current version of the integration should work but if you find some unmanaged pre-processor directive for `UNITY_EDITOR_LINUX` and/or `UNITY_STANDALONE_LINUX` let me know or submit a pull request.

This being said a good place to start digging for these unmanaged cases is by finding occurencies of `UNITY_EDITOR_OSX` and `UNITY_STANDALONE_OSX` in the `Assets/Wwise/` directory in the root of your project (for example with `grep -E "UNITY_EDITOR_OSX|UNITY_STANDALONE_OSX" $(find . -name "*.cs")`) because if there is a case that need to be managed for Mac it probably needs to be managed differently for Linux too.

### Downloader

Currently the downloader does not exist, basically. Any help is appreciated.

I'm still studying the way `bundles` works. Apparently is a system used by the Wwise Launcher to keep track of which `Plugins` and `Packages` are installed so, if you are planning on going down this road this is a good starting point.

Plus the Wwise Launcher is made with Electron; reading the source is a really fast way to get the way things works under the hood.

At some point, hopefully, the Downloader will be able to download the needed `tar.xz` files needed by the installer script to actually install the Wwise Authoring application (which is why you still need to create the offline installer using the Wwise Launcher).

Another thing the downloader should be able to do is to download the Unity Integration Package to be able to bypass the currently needed step of installing the integration under a Mac or Windows system.

## Troubleshooting

### The variable 'tmpString' is declared but never used (in AkUtilities.cs)

This is just a warning.

There is indeed an unused variable named `tmpString` in the method `GetFullPath`; I decided to leave it because I am not sure if it was left accidentally or it is there for a future purpose (probably the first one).

If this warning is too annoying for you nobody is preventing you to get rid of that declaration by yourself.

### There are menu items registered under Edit/Project Settings: Wwise Initialization Settings

This is just a warning too.

I left this alone because it will probably be fixed from Audiokinetic at some point in the future.

### Errors while generating SoundBanks (in Wwise Authoring application and Unity Editor using the Wwise Picker button)

For both the Authoring app and WWise Picker button the problem is the same: the post-generation step went wrong (copying the soundbanks).

This is caused by the fact that most of the `Built-In Macros` defined in Wwise Authoring app, for some reason, `Undefined`. This make the default post-generation step command fail.

A workaround for this is removing these commands from this step.

To make it quick you can modify the file `[PROJECT NAME].wproj` by hand:

```xml
<Property Name="SoundBankPostGenerateCustomCmdDescription" Type="string">
        <ValueList>
                <Value Platform="Windows">Copy Streamed Files</Value>
                <Value Platform="Linux">Copy Streamed Files</Value>
                <Value Platform="iOS">Copy Streamed Files</Value>
                <Value Platform="Android">Copy Streamed Files</Value>
        </ValueList>
</Property>
<Property Name="SoundBankPostGenerateCustomCmdLines" Type="string">
        <ValueList>
                <Value Platform="Windows">"$(WwiseExePath)\CopyStreamedFiles.exe" -info "$(InfoFilePath)" -outputpath "$(SoundBankPath)" -banks "$(SoundBankListAsTextFile)" -languages "$(LanguageList)"</Value>
                <Value Platform="Linux">"$(WwiseExePath)\CopyStreamedFiles.exe" -info "$(InfoFilePath)" -outputpath "$(SoundBankPath)" -banks "$(SoundBankListAsTextFile)" -languages "$(LanguageList)"</Value>
                <Value Platform="iOS">"$(WwiseExePath)\CopyStreamedFiles.exe" -info "$(InfoFilePath)" -outputpath "$(SoundBankPath)" -banks "$(SoundBankListAsTextFile)" -languages "$(LanguageList)"</Value>
                <Value Platform="Android">"$(WwiseExePath)\CopyStreamedFiles.exe" -info "$(InfoFilePath)" -outputpath "$(SoundBankPath)" -banks "$(SoundBankListAsTextFile)" -languages "$(LanguageList)"</Value>
        </ValueList>
</Property>
```

must become this:

```xml
<Property Name="SoundBankPostGenerateCustomCmdDescription" Type="string">
        <ValueList>
                <Value Platform="Windows">Copy Streamed Files</Value>
                <Value Platform="Linux">Copy Streamed Files</Value>
                <Value Platform="iOS">Copy Streamed Files</Value>
                <Value Platform="Android">Copy Streamed Files</Value>
        </ValueList>
</Property>
<Property Name="SoundBankPostGenerateCustomCmdLines" Type="string">
        <ValueList>
                <Value Platform="Windows"></Value>
                <Value Platform="Linux"></Value>
                <Value Platform="iOS"></Value>
                <Value Platform="Android"></Value>
        </ValueList>
</Property>
```

or you can simply delete these withing the Authoring app.

If you don't want to manually copy-paste the Soundbakns into your Unity project any time you need to generate new ones, my suggestion is to remove the directory `GeneratedSoundBanks` and replace it with a symlink pointing to your Unity project (`ln -s [PATH TO UNITY PROJECT ROOT]/Assets/StreamingAssets/Audio/GeneratedSoundBanks/ GeneratedSoundBanks`).

Don't do this the other way around (making a symlink pointing from the Unity project to the Wwise Project) beacuse Unity will complain (and spam in the console) about it.
