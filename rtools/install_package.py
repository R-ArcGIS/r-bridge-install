# Py3 compat layer
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import arcpy
import ctypes
import os
import shutil
import sys

from .bootstrap_r import execute_r
from .github_release import save_url, release_info
from .rpath import r_library_path, r_pkg_path, r_pkg_version, arcmap_exists
from .utils import mkdtemp, set_env_tmpdir
from .fs import getvolumeinfo, hardlinks_supported, junctions_supported

PACKAGE_NAME = 'arcgisbinding'
PACKAGE_VERSION = r_pkg_version()


def install_package(overwrite=False, r_library_path=r_library_path):
    """Install ArcGIS R bindings onto this machine."""
    # pull back stringified bool
    if overwrite or overwrite == 'true':
        overwrite = True
    else:
        overwrite = False
    if not overwrite:
        if PACKAGE_VERSION:
            msg = "The ArcGIS R bridge is installed, and overwrite is disabled."
            arcpy.AddError(msg)
            sys.exit()

    info = arcpy.GetInstallInfo()
    install_dir = info['InstallDir']
    arc_version = info['Version']
    product = info['ProductName']
    arcmap_needs_link = False

    # earlier versions excluded by virtue of not having Python toolbox support
    no_hook_versions = ('10.1', '10.2', '10.2.1', '10.2.2', '10.3.0')
    if arc_version in no_hook_versions and product is not 'ArcGISPro':
        arcpy.AddError("The ArcGIS R bridge requires ArcGIS 10.3.1 or later.")
        sys.exit()

    if arc_version in ('1.0', '1.0.2') and product == 'ArcGISPro':
        arcpy.AddError("The ArcGIS R bridge requires ArcGIS Pro 1.1 or later.")
        sys.exit()

    if product == 'ArcGISPro':
        # detect if we we have a 10.3.1 install that needs linking
        if arcmap_exists("10.3"):
            arcmap_needs_link = True
            arcpy.AddMessage("Pro side by side with 10.3 detected.")

    # set an R-compatible temporary folder, if needed.
    orig_tmpdir = os.getenv("TMPDIR")
    if not orig_tmpdir:
        env_tmpdir = set_env_tmpdir()

    download_url = release_info()[0]
    if download_url is None:
        arcpy.AddError(
            "Unable to get current release information. Check internet connection.")
        sys.exit()

    # we have a release, write it to disk for installation
    arcpy.AddMessage(download_url)
    with mkdtemp() as temp_dir:
        zip_name = os.path.basename(download_url)
        package_path = os.path.join(temp_dir, zip_name)
        save_url(download_url, package_path)
        if os.path.exists(package_path):
            # TODO -- need to do UAC escalation here?
            # call the R installation script
            execute_r('Rcmd', 'INSTALL', package_path)
        else:
            arcpy.AddError("No package found at {}".format(package_path))

    # return TMPDIR to its original value; only need it for Rcmd INSTALL
    set_env_tmpdir(orig_tmpdir)

    # TODO: still do this if installing to Pro, but 10.3.1 is installed, check
    #       registry to find it in this case.


    # at 10.3.1, we _must_ have the bridge installed at the correct location.
    # create a symlink that connects back to the correct location on disk.
    if arc_version == '10.3.1' and product == 'Desktop' or arcmap_needs_link:
        # NOTE: r_package_path currently looks for the registry key for Pro,
        #       will this be an issue?

        r_integration_dir = os.path.join(install_dir, "Rintegration")
        link_dir = os.path.join(r_integration_dir, PACKAGE_NAME)

        # TODO escalate privs here? test on non-admin user
        if not os.path.exists(r_integration_dir):
            os.makedirs(r_integration_dir)

        if os.path.exists(link_dir):
            if junctions_supported(link_dir) or hardlinks_supported(link_dir):
                # os.rmdir uses RemoveDirectoryW, and can delete a junction
                os.rmdir(link_dir)
            else:
                shutil.rmtree(link_dir)

        # set up the link
        r_package_path = r_pkg_path()
        binding_dir = None
        if r_package_path:
            arcpy.AddMessage("Detected package path: {}.".format(
                r_package_path))
            # create POSIX style path as that is what R produces
            # binding_dir = "{}/{}".format(r_package_path, PACKAGE_NAME)
        else:
            arcpy.AddError("Unable to locate R package library. Link failed.")
            sys.exit()

        detect_msg = "ArcGIS 10.3.1 detected."
        if junctions_supported(link_dir) or hardlinks_supported(link_dir):
            arcpy.AddMessage("{} Creating link to package.".format(detect_msg))
            kdll = ctypes.windll.LoadLibrary("kernel32.dll")
            kdll.CreateSymbolicLinkW(link_dir, r_package_path, 1)
        else:
            # working on a non-NTFS volume, copy instead
            vol_info = getvolumeinfo(link_dir)
            arcpy.AddMessage("{} Drive type: {}. Copying package files.".format(
                detect_msg, vol_info[0]))
            # NOTE: this will need to be resynced when the package is updated,
            #       if installed from the R side.
            shutil.copytree(r_package_path, link_dir)

# execute as standalone script, get parameters from sys.argv
if __name__ == '__main__':
    if len(sys.argv) == 2:
        overwrite = sys.argv[1]
    else:
        overwrite = None
    print("library path: {}".format(r_library_path))

    install_package(overwrite=overwrite, r_library_path=r_library_path)
