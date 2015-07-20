# Py3 compat layer
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import arcpy
import os
import sys

from .bootstrap_r import execute_r
from .github_release import release_info
from .install_package import install_package
from .rpath import r_library_path, r_pkg_version
from .utils import versiontuple


def compare_release_versions():
    newer_available = False
    (url, tag) = release_info()
    release = tag.strip('v')

    if versiontuple(release) > versiontuple(r_pkg_version()):
        newer_available = True
    return newer_available


def update_package(r_library_path=r_library_path):
    """Update ArcGIS R bindings on this machine."""
    # TODO make sure that the package isn't loaded before updating?

    info = arcpy.GetInstallInfo()
    install_dir = info['InstallDir']
    arc_version = info['Version']
    product = info['ProductName']

    if arc_version in ('10.1', '10.2', '10.3.0') and product == 'Desktop':
        arcpy.AddError("The ArcGIS R bridge requires ArcGIS 10.3.1 or later.")
        sys.exit()

    if arc_version in ('1.0', '1.0.2') and product == 'ArcGISPro':
        arcpy.AddError("The ArcGIS R bridge requires ArcGIS Pro 1.1 or later.")
        sys.exit()

    # TODO also check for the 10.3.1 package version in case of copy-only?
    if not r_pkg_version():
        arcpy.AddWarning(
            "Package is not installed. First use the \"Install R bindings\" script.")
    elif compare_release_versions():
        arcpy.AddMessage("New release detected! Installing.")
        install_package(overwrite=True, r_library_path=r_library_path)
    else:
        arcpy.AddMessage(
            "Installed package is current or newer than version on GitHub.")

# execute as standalone script, get parameters from sys.argv
if __name__ == '__main__':
    update_package(r_library_path=r_library_path)
