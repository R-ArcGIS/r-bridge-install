from __future__ import unicode_literals

import contextlib
import os
import shutil
import sys
import tempfile
import textwrap


def platform():
    """ Check whether our Python is 32 or 64 bits."""
    platform = None
    if sys.maxsize > 2**32:
        platform = 'x64'
    else:
        platform = 'i386'
    return platform


def dedent(text, ending='\r\n'):
    """Dedent text, allowing multiline comments
    to be properly collapsed."""
    text = text.replace('\n', ending)
    return textwrap.dedent(text)


def versiontuple(v):
    res = None
    if v is not None:
        res = tuple(map(int, (v.split("."))))
    return res


@contextlib.contextmanager
def mkdtemp(suffix='', prefix='tmp', parent_dir=None):
    """A contextlib based wrapper for tempfile.mkdtemp."""
    path = tempfile.mkdtemp(suffix, prefix, parent_dir)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)


def set_env_tmpdir(path=None):
    """Set the system environment value for TMPDIR.

    ArcGIS overrides both TMP and TEMP with its own value on runtime,
    and when R combines this value with its own name suffix it can
    create problems.

    Parameters
    ----------
    path: str, Path to set for TMPDIR environment variable.

    Returns
    -------
    str, resulting value of TMPDIR.
    """
    if path is None:
        # inspect the current value of TMP
        tmp = os.getenv("TMP")
        if tmp is None:
            tmp = os.getenv("TEMP")

        # strip trailing elements, including ArcGIS specific dir
        path = os.path.split(tmp.strip("\\"))[0]

    if os.path.exists(path):
        os.putenv("TMPDIR", path)

    return path
