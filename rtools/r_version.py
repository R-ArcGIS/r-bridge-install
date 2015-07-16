# Py3 compat layer
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

from .bootstrap_r import execute_r


def r_version():
    return execute_r('R', '--version')
