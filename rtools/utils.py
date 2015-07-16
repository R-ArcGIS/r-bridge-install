from __future__ import unicode_literals

import contextlib
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
