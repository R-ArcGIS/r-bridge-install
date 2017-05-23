
from .config import *

from .rpath import (
    arcmap_path,
    r_path,
    r_set_install,
    r_version,
    r_version_dict,
    r_pkg_path,
    r_pkg_version,
    r_lib_path,
    r_user_lib_path,
    r_all_lib_paths,
)
from .bootstrap_r import execute_r
from .install_package import install_package
from .update_package import update_package
