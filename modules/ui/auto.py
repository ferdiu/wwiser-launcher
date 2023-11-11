
import distutils

Menu = None

if not (distutils.spawn.find_executable("kdialog") is None):
    from . import kdialog as Menu
elif not (distutils.spawn.find_executable("zenity") is None):
    from . import zenity as Menu
else:
    raise Exception("Currently console mode is not supported: " +
                    "you need to install one between zenity or " +
                    "kdialog to use this program.")
    from . import console as Menu