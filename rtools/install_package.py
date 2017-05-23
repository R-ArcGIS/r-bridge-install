# Py3 compat layer
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import arcpy

import glob
import os
import shutil
import sys

# create a handle to the windows kernel; want to make Win API calls
try:
    import ctypes
    from ctypes import wintypes
    kdll = ctypes.windll.LoadLibrary("kernel32.dll")
except ImportError:
    msg = "Unable to connect to your Windows configuration, " + \
          "this is likely due to an incorrect Python installation. " + \
          "Try repairing your ArcGIS installation."
    arcpy.AddError(msg)
    sys.exit()

from .bootstrap_r import execute_r
from .github_release import save_url, release_info
from .rpath import (
    r_lib_path,
    r_path,
    r_pkg_path,
    r_pkg_version,
    r_user_lib_path,
    r_version,
    arcmap_exists,
    arcmap_path,
    fnf_exception,
    handle_fnf,
)
from .utils import mkdtemp, set_env_tmpdir
from .fs import getvolumeinfo, hardlinks_supported, junctions_supported
try:
    import winreg
except ImportError:
    # py 2
    import _winreg as winreg

PACKAGE_NAME = 'arcgisbinding'
PACKAGE_VERSION = r_pkg_version()


def bridge_running(product):
    """ Check if the R ArcGIS bridge is running. Installation wil fail
    if the DLL is currently loaded."""
    running = False
    # check for the correct DLL
    if product == 'Pro':
        proxy_name = "rarcproxy_pro.dll"
    else:
        proxy_name = "rarcproxy.dll"
    kdll.GetModuleHandleW.restype = wintypes.HMODULE
    kdll.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    dll_handle = kdll.GetModuleHandleW(proxy_name)  # memory address of DLL
    if dll_handle is not None:
        running = True
    return running


def arcgis_platform():
    """ ArcGIS platform details used internally."""
    info = arcpy.GetInstallInfo()
    install_dir = info['InstallDir']
    arc_version = info['Version']
    if info['ProductName'] == 'ArcGISPro':
        product = 'Pro'
    else:
        # there are other levels, but this is a PYT run from toolbox,
        # so unlikely to be a non-ArcMap context
        product = 'ArcMap'
    return (install_dir, arc_version, product)


def validate_environment(overwrite=None):
    """Make sure we have a version of the product that works, and that
    the library isn't already loaded."""

    (install_dir, arc_version, product) = arcgis_platform()
    # earlier versions excluded by virtue of not having Python toolbox support
    no_hook_versions = ('10.1', '10.2', '10.2.1', '10.2.2', '10.3')
    valid_env = True
    msg = None
    if arc_version in no_hook_versions and product is not 'Pro':
        msg = "The ArcGIS R bridge requires ArcGIS 10.3.1 or later."
        valid_env = False

    if arc_version in ('1.0', '1.0.2') and product == 'Pro':
        msg = "The ArcGIS R bridge requires ArcGIS Pro 1.1 or later."
        valid_env = False

    if not overwrite and PACKAGE_VERSION:
        msg = "The ArcGIS R bridge is already installed, and " + \
             "overwrite is disabled."
        valid_env = False

    # check the library isn't loaded
    if bridge_running(product):
        msg = "The ArcGIS R bridge is currently in-use, restart the " + \
              "application and try again."
        valid_env = False

    if not valid_env:
        arcpy.AddError(msg)
        sys.exit()


def create_registry_entry(product, arc_version):
    """Create a registry link back to the arcgisbinding package."""
    root_key = winreg.HKEY_CURRENT_USER
    if product == 'Pro':
        product_name = "ArcGISPro"
    else:
        product_name = "Desktop{}".format(arc_version)
    reg_path = "SOFTWARE\\Esri\\{}".format(product_name)

    package_key = 'RintegrationProPackagePath'
    link_key = None

    try:
        full_access = (winreg.KEY_WOW64_64KEY + winreg.KEY_ALL_ACCESS)
        # find the key, 64- or 32-bit we want it all
        link_key = winreg.OpenKey(root_key, reg_path, 0, full_access)
    except fnf_exception as error:
        handle_fnf(error)

    if link_key:
        try:
            arcpy.AddMessage("Using registry key to link install.")
            binding_path = "{}\\{}".format(r_lib_path(), "arcgisbinding")
            winreg.SetValueEx(link_key, package_key, 0,
                              winreg.REG_SZ, binding_path)
        except fnf_exception as error:
            handle_fnf(error)


def install_package(overwrite=False, r_library_path=r_lib_path()):
    """Install ArcGIS R bindings onto this machine."""
    if overwrite is True:
        overwrite = True
    else:
        overwrite = False

    (install_dir, arc_version, product) = arcgis_platform()
    arcmap_needs_link = False

    # check that we're in a sane installation environment
    validate_environment(overwrite)

    # detect if we we have a 10.3.1 install that needs linking
    if product == 'Pro' and arcmap_exists("10.3"):
        arcmap_needs_link = True
        msg_base = "Pro side by side with 10.3 detected,"
        if arcmap_path() is not None:
            msg = "{} installing bridge for both environments.".format(msg_base)
            arcpy.AddMessage(msg)
        else:
            msg = "{} but unable to find install path.".format(msg_base) + \
                  "ArcGIS bridge must be manually installed in ArcGIS 10.3."
            arcpy.AddWarning(msg)

    # if we're going to install the bridge in 10.3.1, create the appropriate
    # directory before trying to install.
    if arc_version == '10.3.1' and product == 'ArcMap' or arcmap_needs_link:
        r_integration_dir = os.path.join(arcmap_path(), "Rintegration")
        # TODO escalate privs here? test on non-admin user
        if not os.path.exists(r_integration_dir):
            try:
                write_test = os.path.join(install_dir, 'test.txt')
                with open(write_test, 'w') as f:
                    f.write('test')
                os.remove(write_test)
                os.makedirs(r_integration_dir)
            except IOError:
                arcpy.AddError(
                    "Insufficient privileges to create 10.3.1 bridge directory."
                    " Please start {} as an administrator, by right clicking"
                    " the icon, selecting \"Run as Administrator\", then run this"
                    " script again.".format(product))
                return

    # set an R-compatible temporary folder, if needed.
    orig_tmpdir = os.getenv("TMPDIR")
    if not orig_tmpdir:
        set_env_tmpdir()

    download_url = release_info()[0]
    if download_url is None:
        arcpy.AddWarning(
            "Unable to get current release information."
            " Trying offline installation.")

    local_install = False
    base_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..')
    zip_glob = glob.glob(os.path.join(base_path, "arcgisbinding*.zip"))
    # see if we have a local copy of the binding
    if zip_glob and os.path.exists(zip_glob[0]):
        local_install = True
        zip_path = zip_glob[0]
        zip_name = os.path.basename(zip_path)
    elif not download_url and not local_install:
        arcpy.AddError(
            "Unable to access online package, and no "
            "local copy of package found.")
        return
    else:
        local_install = False
        zip_name = os.path.basename(download_url)

    # check for a network-based R installation
    if r_path() and r_path()[0:2] == r'\\':
        arcpy.AddMessage(
            "R installed on a network path, using fallback installation method.")
        r_local_install = False
    else:
        r_local_install = True

    # we have a release, write it to disk for installation
    with mkdtemp() as temp_dir:
        package_path = os.path.join(temp_dir, zip_name)
        if local_install:
            arcpy.AddMessage("Found local copy of binding, installing from zip")
            shutil.copyfile(zip_path, package_path)
        else:
            save_url(download_url, package_path)
        if os.path.exists(package_path):
            # TODO -- need to do UAC escalation here?
            # call the R installation script
            rcmd_return = 0
            if r_local_install:
                rcmd_return = execute_r('Rcmd', 'INSTALL', package_path)
            if not r_local_install or rcmd_return != 0:
                # if we don't have a per-user library, create one
                r_user_lib = r_user_lib_path()
                if not os.path.exists(r_user_lib):
                    try:
                        arcpy.AddMessage("Creating per-user library directory")
                        os.makedirs(r_user_lib)
                    except OSError:
                        arcpy.AddWarning("Failed to create per-user library.")
                # Can't execute Rcmd in this context, write out a temporary
                # script and run install.packages() from within an R session.
                install_script = os.path.join(temp_dir, 'install.R')
                with open(install_script, 'w') as f:
                    f.write("install.packages(\"{}\", repos=NULL)".format(
                        package_path.replace("\\", "/")))
                rcmd_return = execute_r("Rscript", install_script)
                if rcmd_return != 0:
                    arcpy.AddWarning("Fallback installation method failed.")
        else:
            arcpy.AddError("No package found at {}".format(package_path))
            return

    # return TMPDIR to its original value; only need it for Rcmd INSTALL
    set_env_tmpdir(orig_tmpdir)

    # at 10.4 and Pro <=1.2, if the user has installed a version with a non-
    # numeric patch level (e.g. 3.2.4revised), and the bridge is installed
    # into Program Files, the link will fail. In this case, set the
    # appropriate registry key so that the bridge will still work. Note that
    # this isn't ideal, because it will persist after updates, but it is
    # better than the bridge failing to work at all.
    if (arc_version == '10.4' and product == 'Desktop') or \
            (arc_version in ('1.1', '1.1.1', '1.2')
             and product == 'Pro'):

        if r_version():
            (r_major, r_minor, r_patchlevel) = r_version().split(".")
            # if we have a patchlevel like '4revised' or '3alpha', and
            # the global library path is used, then use the registry key.
            if len(r_patchlevel) > 1 and 'Program Files' in r_library_path:
                # create_registry_entry(product, arc_version)
                msg = ("Currently, the bridge doesn't support patched releases"
                       " (e.g. 3.2.4 Revised) in a global install. Please use"
                       " another version of R.")
                arcpy.AddError(msg)
                return

    # at 10.3.1, we _must_ have the bridge installed at the correct location.
    # create a symlink that connects back to the correct location on disk.
    if arc_version == '10.3.1' and product == 'ArcMap' or arcmap_needs_link:
        link_dir = os.path.join(r_integration_dir, PACKAGE_NAME)

        if os.path.exists(link_dir):
            if junctions_supported(link_dir) or hardlinks_supported(link_dir):
                # os.rmdir uses RemoveDirectoryW, and can delete a junction
                os.rmdir(link_dir)
            else:
                shutil.rmtree(link_dir)

        # set up the link
        r_package_path = r_pkg_path()

        if r_package_path:
            arcpy.AddMessage("R package path: {}.".format(r_package_path))
        else:
            arcpy.AddError("Unable to locate R package library. Link failed.")
            return

        detect_msg = "ArcGIS 10.3.1 detected."
        if junctions_supported(link_dir) or hardlinks_supported(link_dir):
            arcpy.AddMessage("{} Creating link to package.".format(detect_msg))
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
    print("library path: {}".format(r_lib_path()))

    install_package(overwrite=overwrite, r_library_path=r_lib_path())
