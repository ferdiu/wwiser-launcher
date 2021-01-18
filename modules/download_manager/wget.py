
import subprocess
import sys

class DownloadException(Exception):
    def __init__(self, url, method, message):
        self.url = url
        self.method = method
        self.message = message
        super(DownloadException, self).__init__(message)

class DownloadCanceled(DownloadException):
    def __init__(self, url, method):
        super(DownloadCanceled, self).__init__(url, method)

class DownloadProcess(object):
    def __init__(self, pipe, url, method):
        self.pipe = pipe
        self.url = url
        self.method = method

    def wait_finish(self):
        self.pipe.wait()
    
    def is_still_running(self):
        return self.pipe.poll() is None

    def get_output(self):
        for stdout_line in iter(self.pipe.stdout.readline, ""):
            yield stdout_line
        
        self.pipe.stdout.close()

    def get_returncode(self):
        if self.is_still_running(): return None
        return self.pipe.returncode
    
    def cancel(self):
        self.pipe.kill()
        raise DownloadCanceled(self.url, self.method)

class Wget(object):
    common_command = [ "wget", "--quiet", "--no-cookies" ]

    @staticmethod
    def GET(url, output, destination = None, headers = [], wget_stdout = sys.stdout, args = []):
        command = [] + Wget.common_command

        command.append("--show-progress")

        for h in headers:
            command.append("--header")
            command.append(h)
        
        command.append("-O")
        if destination is None:
            command.append("./" + output)
        else:
            command.append(destination + "/" + output)

        for a in args:
            command.append(a)

        command.append(url)

        return DownloadProcess(subprocess.Popen(command, stdout=wget_stdout, universal_newlines=True), url, "GET")

    @staticmethod
    def POST(post_data, url, output = None, destination = None, headers = [], wget_stdout = sys.stdout, args = []):
        command = [] + Wget.common_command

        for h in headers:
            command.append("--header")
            command.append(h)
        
        command.append("--post-data")
        command.append(post_data)

        command.append("-O")
        if output is None:
            command.append("-")
        elif destination is None:
            command.append("./" + output)
        else:
            command.append(destination + "/" + output)
        command.append("--show-progress")

        for a in args:
            command.append(a)

        command.append(url)

        return DownloadProcess(subprocess.Popen(command, stdout=wget_stdout, universal_newlines=True), url, "POST")