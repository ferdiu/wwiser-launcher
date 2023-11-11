# wWiserLauncher

Wwiser Launcher is a set of bash and python scripts for Linux which aims to replace the Wwise Launcher (which is Mac and Windows only).

### Disclaimer

This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by Audiokinetic nor Unity Technologies. All product and company names are the registered trademarks of their original owners. The use of any trade name or trademark is for identification and reference purposes only and does not imply any association with the trademark holder of their product brand.

While the informations and scripts in this project have been verified to the best of my abilities, I can't guarantee that there are no mistakes or errors. If you find any, please report it.

### Advice

Use a version-control system (as `git`) ad commit all your work before applying the Unity Integration Patch.

## Usage

As of today the Wwise Launcher is not needed anymore but the project has to be considered still experimental.

** Currently only `zenity` and `kdialog` are supported (still no console mode available)! They are mandatory to use `wwiser-launcher`! **

### Install Wwise Authroing Application

The process now is really simple:

- execute the Python script `wwiser-launcher.py` (do not cofuse with the Bash script `wwiser-launcher`)
- select `Install Packages` and press `Ok`
- select the desired version of the Authoring App and press `Ok`
- select all the packages you whish to install (at least `Authoring` is needed) and press `Ok`
- select all the Deployment Platforms you are going to develop to (at least `Linux` and a version of `Microsoft/Windows/Visual Studio <VERSION HERE>` is needed) and press `Ok`
- select all the plugins you whish to install and press `Ok`
- confirm installation
- select where to install the launch script for the installed version (a good place might be `~/.bin` directory, if unsure select `Place it in the home to move it later` to create it in your home)
- now you should be able to launch the authoring app using the script created at the previous step

Keep in mind that between each step the script needs to download _Bundles information_ from Audiokinetic servers so you may have to wait some time depending on the speed of your internet connection; I am working on making this process visible but this feature is still under construction.

### Apply Unity Integration Patch

Unity Integration patch assumes that you installed the Wwise Authoring application in your wine directory. Most of this work is done with this in mind.

- execute the Python script `wwiser-launcher.py` (do not cofuse with the Bash script `wwiser-launcher`)
- select `Apply Unity Integration` and press `Ok`
- select the proper version of the Authoring App you are using to edit the wwise project of your unity project and press `Ok`
- select the packages you want to install in you project (it is recommended to use install at least `Unity Integration` and `Unity Integration Extensions`) and press `Ok`
- select all the Deployment Platforms you are going to develop to and press `Ok`
- confirm installation
- select the rott directory of your project
- just wait while the program downloads the integration scripts, installs them into the unity project, applies the patch (if available for the Unity Integration Version downloaded) and executes the setup (all of this steps may require sometime, be patient)

For an explaination of what the patches do see this [text file](unity_integration/patches/README.txt).

## Dependencies and Requirements

No root permission is needed.

The scripts were originally tested under Debian 10 GNU/Linux (Linux kernel 4.19.0) with Wine Staging (v6.0-rc1) but currently they are being developed under Fedora Linux 38 (Linux kernel 6.3.5) with Wine Staging (v8.19). I think the bottleneck in terms of compatibility could be Wine so, if you encounter any issue and you decide to open an issue, please be sure to post your exact version.

- Wine Staging (v6.0-rc1 or above)
- make sure to have in your `PATH` the `winepath` util to convert path between unix and wine paths

Used inside scripts

- `tar` (for archives extraction during installation)
- `sed` (currently tested only with the GNU version but there is no reason to think it would not work with the standard version)

The downloader needs:

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

The downloader finally works but it still needs polishing. Any help is appreciated.

I'm still studying the way `bundles` works. Apparently it is a system used by the Wwise Launcher to keep track of which `Plugins` and `Packages` are installed so, if you are planning on going down this road this is a good starting point.

Plus the Wwise Launcher is made with Electron; reading the source is a really fast way to get the way things works under the hood.

## Troubleshooting

### Problems when launching Authroing app

If the installed Authoring App does not start it could mean that there might be some missing libraries in your `wine` installation: one of them could be `mfc140u.dll` (64bit).

The simplies way to install it is by using `winecfg`. See [wine documnetation](https://wiki.winehq.org/Winecfg#Libraries) for more info.

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

## TODO

- [ ] ask to the user whether he/she wants to install the Authoring App in the default `WINEPREFIX` or allow he/she to select/create a new one
- [ ] login
- [ ] create a `requirements.txt` to install automatically python dependencies
- [ ] allow user to choose between `curl` and `wget` to manage downloads (currently only `wget` is supported)
- [ ] inform the user about Eulas and let him/her accept them
- [ ] integration for editors
    - [X] unity integration
        - [ ] automatically change to winepath-like the value of `WwiseInstallationPathWindows` in `WwiseSettings.xml`
        - [ ] automatically link GeneratedSoundBanks directory in wwise project to the Unity Project directory in StreamingAssets and remove "extra steps" from Wwise Project Settings (which cause errors when generating soundbanks)
    - [ ] unreal integration
    - [ ] godot integration (see [wwise-godot-integration](https://github.com/alessandrofama/wwise-godot-integration))
- [ ] ui development
    - [X] zenity
        - [ ] show download progress
    - [X] kdialog
        - [ ] show download progress
    - [ ] console
- [ ] populate install-entry.json "children" field during installation procedure
- [ ] use a json to keep track of what was already installed
- [ ] uninstaller for authoring app (need previous point to be completed)
- [ ] consider porting to python all bash scripts[\*](#bash-deprecation)

<a name="bash-deprecation">\*</a>I really do not like Python but when it comes to portability of software it is almost a certainty. This is way I ended up using this for this project. My first choice was Bash scripting but, when I realized how big this project was becoming, a change was needed: Bash is really powerful as system managing tool but it really is not comfortable enough when it comes to parsing and storing JSONs files. This was basically effort-free in Python.
