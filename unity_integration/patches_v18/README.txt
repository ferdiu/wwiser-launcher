This file is just a summury of the patches that need to be applied to the unity project after the Wwise Luncher integration.


If you ended up reading this file you probably encountered some problem.
I will never get tired of say this:

1) MAKE SURE YOU PROPERLY INSTALLED WINE (AND WINEPATH)
   AND THAT IT IS IN YOUR PATH ENV VARIABLE!
2) THESE SCRIPTS WERE TESTED IN DEBIAN 10 WITH WINE-STAGING (v6.0)
   SO IT IS NOT GRANTED TO WORK ON PREVIOUS VERSIONS
3) I TRIED TO USE ONLY PRE-INSTALLED TOOLS (WHICH SHOULD BE AVAILABLE
   IN MOST DISTROS) FOR MOST OF THE SCRIPTS BUT IT IS POSSIBLE YOU WILL
   NEED TO INSTALL SOME BEFORE EXECUTING (I WILL TRY TO KEEP TRACK OF THE
   UTILS NEEDED INSIDE THE README.md OF THIS REPOSITORY)
4) THESE SCRIPTS WERE CREATED FOR A PROJECT USING Wwise v2019.1.10, AT
   THE TIME OF YOUR READING MAY BE NEEDED MORE CHANGES OR CHANGES IN HERE
   MAY BE OBSOLETE


What you need to know to read this file:

===== TITLE =====                                                   <-- Section title
# n|     some code here                                             <-- Changes made in files
// SUMMARY:                                                         <-- Brief summary of the change and why it is needed
Files [ORIGINAL FILE PATH] and [PATCHED FILE PATH] are different    <-- Which file(s) needs to be modified


============================================== PATCHES ==============================================

===== GENERATED =====

# In the Generated APIs change first line
# from:
# 1| #if UNITY_STANDALONE_LINUX && ! UNITY_EDITOR
# to
# 1| #if (UNITY_STANDALONE_LINUX && ! UNITY_EDITOR) || UNITY_EDITOR_LINUX

// SUMMARY: Compile these scripts in UNITY_EDITOR_LINUX too.

Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkAudioAPI_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkAudioAPI_Linux.cs are different
Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkCommunicationSettings_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkCommunicationSettings_Linux.cs are different
Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkMemPoolAttributes_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkMemPoolAttributes_Linux.cs are different
Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkPlatformInitSettings_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkPlatformInitSettings_Linux.cs are different
Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEngine_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEngine_Linux.cs are different
Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEnginePINVOKE_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkSoundEnginePINVOKE_Linux.cs are different
Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkThreadProperties_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkThreadProperties_Linux.cs are different
Files Original/Assets/Wwise/Deployment/API/Generated/Linux/AkUnityPlatformSpecificSettings_Linux.cs and Patched/Assets/Wwise/Deployment/API/Generated/Linux/AkUnityPlatformSpecificSettings_Linux.cs are different

===== HANDWRITTEN =====

# Insert at row 249

# after:
# 248|         return System.IO.Path.Combine(UnityEngine.Application.dataPath, "Wwise", "Deployment", "Plugins", "Mac", "DSP");

# add lines:
# 249| #elif UNITY_EDITOR_LINUX
# 250|         return System.IO.Path.Combine(UnityEngine.Application.dataPath, "Wwise", "Deployment", "Plugins", "Linux", "x86_64", "DSP");

# will look like:
# 248|         return System.IO.Path.Combine(UnityEngine.Application.dataPath, "Wwise", "Deployment", "Plugins", "Mac", "DSP");
# 249| #elif UNITY_EDITOR_LINUX
# 250|         return System.IO.Path.Combine(UnityEngine.Application.dataPath, "Wwise", "Deployment", "Plugins", "Linux", "x86_64", "DSP");
# 251| #elif UNITY_STANDALONE_WIN

// SUMMARY: UNITY_EDITOR_LINUX needs to know where the plugins directory is.

Files Original/Assets/Wwise/Deployment/API/Handwritten/Common/AkCommonPlatformSettings.cs and Patched/Assets/Wwise/Deployment/API/Handwritten/Common/AkCommonPlatformSettings.cs are different

# 193| #elif UNITY_EDITOR_OSX
# 194| 		if (!string.IsNullOrEmpty(settings.WwiseInstallationPathMac))
# 195| 			result = System.IO.Path.Combine(settings.WwiseInstallationPathMac, "Contents/Tools/WwiseCLI.sh");
=>added part begin
# 196| #elif UNITY_EDITOR_LINUX
# 197| 		if (!string.IsNullOrEmpty(settings.WwiseInstallationPathWindows))
# 198| 		{
# 199| 			result = settings.WwiseInstallationPathWindows + @"\Authoring\x64\Release\bin\WwiseCLI.exe";
# 200| 
# 201| 			if (!System.IO.File.Exists(WineHelper.ConvertWinePathToUnix(result)))
# 202| 				result = settings.WwiseInstallationPathWindows + @"\Authoring\Win32\Release\bin\WwiseCLI.exe";
# 203| 		}
# 204| 
# 205| 		if (result != null && System.IO.File.Exists(WineHelper.ConvertWinePathToUnix(result)))
# 206| 			return result;
=>added part end
# 207| #endif
# 208| 
# 209|  		if (result != null && System.IO.File.Exists(result))

@@ -228,12 +239,19 @@
# 228| #elif UNITY_EDITOR_OSX
# 229| 		var command = "/bin/sh";
# 230| 		var arguments = "\"" + wwiseCli + "\"";
=>added part begin
# 231|+#elif UNITY_EDITOR_LINUX
# 232|+		var command = WineHelper.wineBin;
# 233|+		var arguments = "\"" + wwiseCli + "\"";
=>added part end
# 234| #else
# 235| 		var command = "";
# 236| 		var arguments = "";
# 237| #endif
# 238| 
=>added part begin
# 239|+#if UNITY_EDITOR_LINUX
# 240|+		arguments += " \"" + WineHelper.ConvertUnixPathToWine(wwiseProjectFullPath) + "\"";
# 241|+#else
=>added part end
# 242| 		arguments += " \"" + wwiseProjectFullPath + "\"";
=>added part begin
# 243|+#endif
=>added part end
# 243| 
# 244| 		if (platforms != null)
# 245| 		{

NB: LINE NUMBERS MAY DIFFER FROM THESE, DO NOT TRUST THEM!

// SUMMARY: Use the WineHelper script to make the "Generate Soundbanks" button work in Wwise Picker Window.

Files Original/Assets/Wwise/Deployment/API/Handwritten/Common/AkUtilities.cs and Patched/Assets/Wwise/Deployment/API/Handwritten/Common/AkUtilities.cs are different

# Change the following line
# from:
# 37| #elif UNITY_STANDALONE_LINUX
# to:
# 37| #elif UNITY_EDITOR_LINUX || (UNITY_STANDALONE_LINUX && !UNITY_EDITOR)
# will look like:
# 35| #elif UNITY_EDITOR_OSX || (UNITY_STANDALONE_OSX && !UNITY_EDITOR)
# 36| 		platformSubDir = "Mac";
# 37| #elif UNITY_EDITOR_LINUX || (UNITY_STANDALONE_LINUX && !UNITY_EDITOR)
# 38| 		platformSubDir = "Linux";
# 39| #elif UNITY_XBOXONE

// SUMMARY: This is needed for cross-compile your game in Unity Editor for other platforms.
//          (otherwise the "Undefined platform sub-folder" dir will be used to generate
//          soundbanks if a different platform is setted in "Build settings" menu)

Files Original/Assets/Wwise/Deployment/API/Handwritten/Common/AkBasePathGetter.cs and Patched/Assets/Wwise/Deployment/API/Handwritten/Common/AkBasePathGetter.cs are different


===== PICKER =====

# Change error message string initialization at row 53
# from:
# 53| #if UNITY_EDITOR_WIN
# to:
# 53| #if UNITY_EDITOR_WIN || UNITY_EDITOR_LINUX

// SUMMARY: Use the same errorMessage as Windows if the path to Wwise application is not inserted in Wwise Settings.

Files Original/Assets/Wwise/Editor/WwiseWindows/AkWwisePicker.cs and Patched/Assets/Wwise/Editor/WwiseWindows/AkWwisePicker.cs are different

===== PLUGIN ACTIVATOR =====

# Add following lines before "Mac" case:
# 549|                 case "Linux":
# 550|                     editorCPU = splitPath[5];
# 551|                     pluginConfig = splitPath[6];
# 552|                     editorOS = "Linux";
# 553|                     break;
# 554|

// SUMMARY: This is needed to tell Unity Editor where to find libAkSoundEngine.so library otherwise you will get an
//          Exception (DllNotFoundException) and the Sound Engine will not be initialized inside the editor.

Files Original/Assets/Wwise/Editor/WwiseSetupWizard/AkPluginActivator.cs and Patched/Assets/Wwise/Editor/WwiseSetupWizard/AkPluginActivator.cs are different
