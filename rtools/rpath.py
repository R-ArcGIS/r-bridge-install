from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from contextlib import contextmanager
from collections import OrderedDict
import ctypes.wintypes
import datetime
import errno
import getpass
import logging
import os

try:
    import winreg
except ImportError:
    # py 2
    import _winreg as winreg

log = logging.getLogger(__name__)

# cyptes constants
CSIDL_PROFILE = 40
SHGFP_TYPE_CURRENT = 0


# TODO re-intergrate this.
@contextmanager
def ignored(*exceptions):
    """Use contextlib to ignore all windows specific errors.
       These are generally encountered from missing registry keys,
       and can safely be ignored in most circumstances."""
    try:
        yield
    except exceptions:
        pass

fnf_exception = getattr(__builtins__,
                        'FileNotFoundError', WindowsError)


def log_exception(err):
    """Make sure we can properly decode the exception,
       otherwise non-ASCII characters will cause a
       crash in the exception despite our intent to
       only log the results."""

    # enc = locale.getpreferredencoding() or 'ascii'
    log.debug("Exception generated:")
    log.debug(err)
    # log.debug(error.encode(enc, 'ignore').decode('utf-8')))


def _documents_folder():
    """ Get the users' documents folder, which is where R will place
        its default user-specific 'personal' library.

        Returns: full path of user library."""

    # first, check if the user has an R_USER variable initialized.
    documents_folder = _environ_path("R_USER")

    if not documents_folder:
        # Call SHGetFolderPath using ctypes.
        ctypes_buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(
            0, CSIDL_PROFILE, 0, SHGFP_TYPE_CURRENT, ctypes_buffer)
        # This isn't a language-independent way, but CSIDL_PERSONAL gets
        # the wrong path.
        # TODO: Test in non-English locales.
        documents_folder = os.path.join(ctypes_buffer.value, "Documents")

    return documents_folder


def _user_sids():
    """Map between usernames and the related SID."""
    user_sids = {}

    root_key = winreg.HKEY_LOCAL_MACHINE
    reg_path = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList"

    try:
        log.info("OpenKey on {}, with READ + WOW64\n".format(reg_path))
        sid_reg = winreg.OpenKey(root_key, reg_path,
                                 0, (winreg.KEY_WOW64_64KEY +
                                     winreg.KEY_READ))

    except fnf_exception as error:
        log_exception(error)
        if error.errno == errno.ENOENT:
            pass
        else:
            raise

    if sid_reg:
        subkey_count = winreg.QueryInfoKey(sid_reg)[0]
        for pos in range(subkey_count):
            try:
                sid = winreg.EnumKey(sid_reg, pos)
            except:
                pass
            if sid:
                profile_path_key = "{}\\{}".format(reg_path, sid)
                try:
                    profile_path_reg = winreg.OpenKey(
                        root_key, profile_path_key, 0,
                        (winreg.KEY_READ | winreg.KEY_WOW64_64KEY))

                    profile_path = winreg.QueryValueEx(
                        profile_path_reg, "ProfileImagePath")[0]

                    username = profile_path.split("\\")[-1]
                    user_sids[username] = sid
                except:
                    pass

    return user_sids


def _user_hive(username=None):
    """Find the registry hive for a particular user."""
    hive = None
    sids = _user_sids()
    if username and username in sids:
        sid = sids[username]
        root_key = winreg.HKEY_USERS
        try:
            hive = winreg.OpenKey(root_key, sid,
                                  0, (winreg.KEY_WOW64_64KEY +
                                      winreg.KEY_READ))
        except:
            pass
    return hive


def _environ_path(var=None):
    """ Check if an environment variable is an existing path."""
    path = None
    if var and var in os.environ:
        var_path = os.environ[var]
        if os.path.exists(var_path):
            path = var_path

    return path


def r_path():
    """Find R installation path from registry."""
    r_install_path = None

    # set an epoch for a Windows FILETIME object
    epoch = datetime.datetime(1601, 1, 1)

    root_keys = OrderedDict((
        # if we have a user hive, also check that first.
        ('HKU', _user_hive(getpass.getuser())),
        ('HKCU', winreg.HKEY_CURRENT_USER),
        ('HKLM', winreg.HKEY_LOCAL_MACHINE),
    ))
    r_reg_paths = ["SOFTWARE\\R-core\\R",
                   "SOFTWARE\\R-core\\R64",
                   "SOFTWARE\\Wow6432Node\\R-Core\\R",
                   "SOFTWARE\\Wow6432Node\\R-Core\\R64"]

    for (key_name, root_key) in list(root_keys.items()):
        for r_path in r_reg_paths:
            r_reg = None

            try:
                log.info("OpenKey on {}, with READ + WOW64\n".format(
                    r_path))
                r_reg = winreg.OpenKey(root_key, r_path,
                                       0, (winreg.KEY_WOW64_64KEY +
                                           winreg.KEY_READ))
            except fnf_exception as error:
                log_exception(error)
                if error.errno == errno.ENOENT:
                    pass
                else:
                    raise

            if r_reg:
                log.info("Successfully found {}".format(r_path))

                try:
                    log.info("Looking for InstallPath.")
                    r_install_path = winreg.QueryValueEx(r_reg, "InstallPath")[0]
                except fnf_exception as error:
                    log_exception(error)
                    if error.errno == errno.ENOENT:
                        pass
                    else:
                        raise

                if not r_install_path:
                    log.debug("Top-level install path not defined. " +
                              "Checking version-specific locations.")
                    # Can't find the install path as a top-level value.
                    # Inspect the children keys for versions, and use the most
                    # recently installed one as the correct R installation.
                    max_time = epoch
                    try:
                        subkey_count = winreg.QueryInfoKey(r_reg)[0]
                    except:
                        subkey_count = 10
                    for pos in range(subkey_count):
                        # TODO ensure this is robust to errors
                        with ignored(WindowsError):
                            log.info("checking EnumKey pos {}".format(pos))
                            r_base_key = winreg.EnumKey(r_reg, pos)

                            # test for the right path based on age
                            if r_base_key:
                                r_version_key = "{}\\{}".format(
                                    r_path, r_base_key)
                                r_version_reg = winreg.OpenKey(
                                    root_key, r_version_key, 0,
                                    (winreg.KEY_READ |
                                     winreg.KEY_WOW64_64KEY))
                                r_install_path = winreg.QueryValueEx(
                                    r_version_reg, "InstallPath")[0]
                                r_version_info = winreg.QueryInfoKey(
                                    r_version_reg)
                                r_install_time = epoch + datetime.timedelta(
                                    microseconds=r_version_info[2]/10)
                                if max_time < r_install_time:
                                    max_time = r_install_time
    log.info("Final R install path: {}".format(r_install_path))
    return r_install_path

r_install_path = r_path()


def r_version():
    r_version = None
    r_path_l = r_install_path
    if r_path_l is not None:
        r_version = r_path_l.split('-')[1]
    return r_version

r_version_info = r_version()


def r_all_lib_paths():
    """ Package library, locates all known library
        paths used for R packages."""

    libs_path = []
    # check R_LIBS_USER first
    if _environ_path("R_LIBS_USER"):
        libs_path.append(_environ_path("R_LIBS_USER"))

    if r_version_info:
        # user's R library in Documents/R/win-library/R-x.x/
        (r_major, r_minor, r_patch) = r_version_info.split(".")

        r_user_library_path = os.path.join(
            _documents_folder(), "R", "win-library",
            "{}.{}".format(r_major, r_minor))
        if os.path.exists(r_user_library_path):
            libs_path.append(r_user_library_path)

    # Next, check the value of R_LIBS -- users may set this
    # instead of the (more specific) R_LIBS_USER
    if _environ_path("R_LIBS"):
        libs_path.append(_environ_path("R_LIBS"))

    # lastly, check for possible site libraries.
    # NOTE: Requires elevated privileges to write to

    if _environ_path("R_LIBS_SITE"):
        libs_path.append(_environ_path("R_LIBS_SITE"))

    # R library in Program Files/R-x.xx/library
    if r_install_path is not None:
        r_install_lib_path = os.path.join(
            r_install_path, "library")

        if os.path.exists(r_install_lib_path):
            libs_path.append(r_install_lib_path)

    return libs_path

r_all_library_paths = r_all_lib_paths()


def r_lib_path():
    """ Package library, locates the highest-priority
        library path used for R packages."""
    lib_path = None
    all_libs = r_all_library_paths
    if len(all_libs) > 0:
        lib_path = all_libs[0]
    return lib_path

r_library_path = r_lib_path()


def r_pkg_path():
    """
    Package path search. Locations searched:
     - HKCU\\Software\\Esri\\ArcGISPro\\RintegrationProPackagePath
     - [MYDOCUMENTS]/R/win-library/[3-9].[0-9]/ - default for user R packages
     - [ArcGIS]/Resources/Rintegration/arcgisbinding
    """
    package_path = None
    package_name = 'arcgisbinding'

    root_key = winreg.HKEY_CURRENT_USER
    reg_path = "SOFTWARE\\Esri\\ArcGISPro"
    package_key = 'RintegrationProPackagePath'
    pro_reg = None

    try:
        # find the key, 64- or 32-bit we want it all
        pro_reg = winreg.OpenKey(
            root_key, reg_path, 0,
            (winreg.KEY_READ | winreg.KEY_WOW64_64KEY))
    except fnf_exception as error:
        if error.errno == errno.ENOENT:
            pass
        else:
            raise

    if pro_reg:
        try:
            # returns a tuple of (value, type)
            package_path_key = winreg.QueryValueEx(pro_reg, package_key)
            package_path_raw = package_path_key[0]
            if os.path.exists(package_path_raw):
                package_path = package_path_raw
        except fnf_exception as error:
            if error.errno == errno.ENOENT:
                pass
            else:
                raise

    # iterate over all known library path locations,
    # and check for our package in each.
    for lib_path in r_all_library_paths:
        possible_package_path = os.path.join(lib_path, package_name)
        if os.path.exists(possible_package_path):
            package_path = possible_package_path
            # we want the highest-priority library, stop here
            break

    # fallback -- <ArcGIS Install>/Rintegration/arcgisbinding
    if not package_path:
        import arcpy
        arc_install_dir = arcpy.GetInstallInfo()['InstallDir']
        arc_package_dir = os.path.join(
            arc_install_dir, 'Rintegration', package_name)
        if os.path.exists(arc_package_dir):
            package_path = arc_package_dir

    return package_path

r_package_path = r_pkg_path()


def r_pkg_version():
    version = None
    r_package_path = r_pkg_path()
    if r_package_path:
        desc_path = os.path.join(r_package_path, 'DESCRIPTION')
        if os.path.exists(desc_path):
            with open(desc_path) as desc_f:
                for line in desc_f:
                    try:
                        (key, value_raw) = line.strip().split(':')
                    except:
                        # gulp
                        pass
                    if key == 'Version':
                        version = value_raw.strip()
    return version

r_package_version = r_pkg_version()


def arcmap_exists(version=None):
    root_key = winreg.HKEY_CURRENT_USER
    reg_base = "SOFTWARE\\Esri"
    if not version:
        version = "10.3"
    package_key = "Desktop{}".format(version)

    reg_path = "{}\\{}".format(reg_base, package_key)
    arcmap_reg = None
    installed = False
    try:
        # find the key, 64- or 32-bit we want it all
        arcmap_reg = winreg.OpenKey(
            root_key, reg_path, 0,
            (winreg.KEY_READ | winreg.KEY_WOW64_64KEY))
    except fnf_exception as error:
        log_exception(error)
        if error.errno == errno.ENOENT:
            pass
        else:
            raise

    if arcmap_reg:
        installed = True

    return installed


def arcmap_path(version=None):
    """Path to ArcGIS Installation."""

    arcmap_path = None

    if not version:
        version = "10.3"
    package_key = "Desktop{}".format(version)

    root_key = winreg.HKEY_LOCAL_MACHINE
    arc_reg_paths = [
        "SOFTWARE\\ESRI\\{}".format(package_key),
        "SOFTWARE\\Wow6432Node\\ESRI\\{}".format(package_key)
    ]

    arcmap_reg = None
    for reg_path in arc_reg_paths:
        try:
            # find the key, 64- or 32-bit we want it all
            arcmap_reg = winreg.OpenKey(
                root_key, reg_path, 0,
                (winreg.KEY_READ | winreg.KEY_WOW64_64KEY))
        except fnf_exception as error:
            log_exception(error)
            if error.errno == errno.ENOENT:
                pass
            else:
                raise

        if arcmap_reg:
            try:
                # returns a tuple of (value, type)
                arcmap_path_key = winreg.QueryValueEx(arcmap_reg, "InstallDir")
                arcmap_path_raw = arcmap_path_key[0]
                if os.path.exists(arcmap_path_raw):
                    arcmap_path = arcmap_path_raw.strip('\\')
            except fnf_exception as error:
                log_exception(error)
                if error.errno == errno.ENOENT:
                    pass
                else:
                    raise

    return arcmap_path

arcmap_install_path = arcmap_path()
