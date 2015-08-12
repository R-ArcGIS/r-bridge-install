# Copyright (c) 2012-2013, the Mozilla Foundation and others.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# From the NTFS project: https://github.com/sid0/ntfs

import ctypes
from ctypes import POINTER, WinError, byref
from ctypes.wintypes import DWORD, BOOL

LPDWORD = POINTER(DWORD)

FILE_SUPPORTS_HARD_LINKS = 0x00400000
FILE_SUPPORTS_REPARSE_POINTS = 0x00000080

MAX_PATH = 260

INVALID_HANDLE_VALUE = -1

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364996
GetVolumePathName = ctypes.windll.kernel32.GetVolumePathNameW
GetVolumePathName.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, DWORD]
GetVolumePathName.restype = BOOL

# http://msdn.microsoft.com/en-us/library/windows/desktop/aa364993
# note: invludes full fsflags listing
GetVolumeInformation = ctypes.windll.kernel32.GetVolumeInformationW
GetVolumeInformation.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, DWORD,
                                 LPDWORD, LPDWORD, LPDWORD, ctypes.c_wchar_p,
                                 DWORD]
GetVolumeInformation.restype = BOOL


def getvolumeinfo(path):
    """
    Return information for the volume containing the given path. This is going
    to be a pair containing (file system, file system flags).
    """

    # Add 1 for a trailing backslash if necessary, and 1 for the terminating
    # null character.
    volpath = ctypes.create_unicode_buffer(len(path) + 2)
    rv = GetVolumePathName(path, volpath, len(volpath))
    if rv == 0:
        raise WinError()

    fsnamebuf = ctypes.create_unicode_buffer(MAX_PATH + 1)
    fsflags = DWORD(0)
    rv = GetVolumeInformation(volpath, None, 0, None, None, byref(fsflags),
                              fsnamebuf, len(fsnamebuf))
    if rv == 0:
        raise WinError()

    return (fsnamebuf.value, fsflags.value)


def hardlinks_supported(path):
    (fsname, fsflags) = getvolumeinfo(path)
    # FILE_SUPPORTS_HARD_LINKS isn't supported until Windows 7, so also check
    # whether the file system is NTFS
    return bool((fsflags & FILE_SUPPORTS_HARD_LINKS) or (fsname == "NTFS"))


def junctions_supported(path):
    (fsname, fsflags) = getvolumeinfo(path)
    return bool(fsflags & FILE_SUPPORTS_REPARSE_POINTS)
