using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public static class WineHelper
{
    private static string _wineBin = null;
    private static string _winepathBin = null;
    private static string _realpathBin = null;

    public static string wineBin { get { 
        if (_wineBin == null || _wineBin == "") return _wineBin = FindBinaryInEnvPath("wine");
        return _wineBin;
    } }
    public static string winepathBin { get {
        if (_winepathBin == null || _winepathBin == "") return _winepathBin = FindBinaryInEnvPath("winepath");
        return _winepathBin;
    } }
    public static string realpathBin { get {
        if (_realpathBin == null || _realpathBin == "") return _realpathBin = FindBinaryInEnvPath("realpath");
        return _realpathBin;
    } }

    private static string FindBinaryInEnvPath(string binary)
    {
        char[] splitter = { ':' };
        string[] paths = System.Environment.GetEnvironmentVariable("PATH").Split(splitter);

        foreach (string p in paths)
            if (System.IO.File.Exists(p + "/" + binary)) {
                Debug.Log("Found " + binary + " binary at " + p + "/" + binary);
                return p + "/" + binary;
            }

        return "";
    }

    private static string ExecuteAndGetOutput(string binary, string arguments)
    {
        string output = "";

        var proc = new System.Diagnostics.Process 
        {
            StartInfo = new System.Diagnostics.ProcessStartInfo
            {
                FileName = binary,
                Arguments = arguments,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
            }
        };

        proc.Start();
        while (!proc.StandardOutput.EndOfStream)
        {
            output = proc.StandardOutput.ReadLine();
        }

        return output;
    }

    public static string ConvertWinePathToUnix(string winePath, bool realPath = false)
    {
        if (!System.IO.File.Exists(winepathBin)) {
            Debug.Log("Error: winepath not found! Is Wine installed in the system?");
            return winePath;
        }

        if (realPath)
            return ExecuteAndGetOutput(realpathBin, "\"" + ExecuteAndGetOutput(winepathBin, "-u \"" + winePath + "\"") + "\"");
        else
            return ExecuteAndGetOutput(winepathBin, "-u \"" + winePath + "\"");
    }

    public static string ConvertUnixPathToWine(string unixPath)
    {
        if (!System.IO.File.Exists(winepathBin)) {
            Debug.Log("Error: winepath not found! Is Wine installed in the system?");
            return unixPath;
        }

        return ExecuteAndGetOutput(winepathBin, "-w \"" + unixPath + "\"");
    }

}
