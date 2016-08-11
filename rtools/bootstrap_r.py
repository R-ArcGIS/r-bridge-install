# Py3 compat layer
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import os
import subprocess
import sys
import arcpy

from .rpath import r_path
from .utils import platform

PY2 = sys.version_info[0] == 2


def execute_r(command='Rcmd', *args):
    if r_install_valid():
        valid_commands = ['R', 'Rcmd', 'Rscript']
        if command not in valid_commands:
            arcpy.AddError("Invalid R command, '{}.exe'.".format(command))
            return

        rcommand_exe = "{}.exe".format(command)
        rcommand_path = os.path.join(
            r_path(), 'bin', platform(), rcommand_exe)
        rcommand_dir = os.path.dirname(rcommand_path)
        # Change directory prior to execution, have a user who continuously
        # gets "'C:\Program' is not recognized as an internal or external
        # command, operable program or batch file."
        if os.path.exists(rcommand_dir):
            parts = [rcommand_dir, os.getenv("PATH")]
            if PY2:
                set_path = ";".join(parts).encode("utf8", "replace")
            else:
                set_path = ";".join(parts)
            os.putenv("PATH", set_path)

        if r_command_valid(rcommand_path):
            command_parts = [rcommand_exe] + list(args)
            arcpy.AddMessage(subprocess.list2cmdline(command_parts))

            if command is 'Rscript':
                script_base = os.path.dirname(os.path.realpath(__file__))
                # if we have a script, it should be the first passed arg
                script_path = os.path.join(script_base, args[0])
                if not os.path.exists(script_path):
                    arcpy.AddError("Couldn't locate requested script, "
                                   "'{}'.".format(script_path))
                    return
                else:
                    command_parts[1] = script_path

            process = subprocess.Popen(command_parts,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True,
                                       cwd=rcommand_dir)
            while process.poll() is None:
                stdout_msg = process.stdout.readline().strip()
                if stdout_msg:
                    arcpy.AddMessage(stdout_msg)
                stderr_msg = process.stderr.readline().strip()
                if stderr_msg:
                    # highlight standard error as warnings
                    arcpy.AddWarning(stderr_msg)

            if process.returncode != 0:
                arcpy.AddWarning("R command returned non-zero exit status.")
            return process.returncode


def path_exists(path):
    valid = False
    if path and os.path.exists(path):
        valid = True
    return valid


def r_install_valid():
    valid = path_exists(r_path())
    if not valid:
        arcpy.AddError("Unable to find valid R installation. Please install R.")
    return valid


def r_command_valid(command_path):
    valid = path_exists(command_path)
    if not valid:
        arcpy.AddError("Unable to locate requested R command: {}".format(
            command_path))
    return valid
