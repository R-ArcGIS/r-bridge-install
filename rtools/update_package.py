# Py3 compat layer
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import arcpy

from .github_release import release_info
from .install_package import install_package, validate_environment
from .rpath import r_lib_path, r_pkg_version
from .utils import versiontuple


def compare_release_versions():
    newer_available = False
    (url, tag) = release_info()
    release = tag.strip('v')

    if versiontuple(release) > versiontuple(r_pkg_version()):
        newer_available = True
    return newer_available


def update_package(r_library_path=r_lib_path()):
    """Update ArcGIS R bindings on this machine."""

    # check that we're in a sane installation environment
    validate_environment(overwrite=True)

    if r_pkg_version() is None:
        arcpy.AddWarning(
            "Package is not installed. First use the \"Install R bindings\" script.")
    else:
        if compare_release_versions():
            arcpy.AddMessage("New release detected! Installing.")
            install_package(overwrite=True, r_library_path=r_library_path)
        else:
            msg = "The installed ArcGIS R package (version " + \
                  "{}) is the current version on GitHub.".format(r_pkg_version())
            arcpy.AddMessage(msg)

# execute as standalone script, get parameters from sys.argv
if __name__ == '__main__':
    update_package(r_library_path=r_lib_path())
