
from .config import *

from .rpath import (
    arcmap_install_path,
    r_install_path,
    r_version_info,
    r_package_path,
    r_package_version,
    r_library_path,
    r_all_library_paths,
)
from .bootstrap_r import execute_r
from .install_package import install_package
from .update_package import update_package
from .r_version import r_version
