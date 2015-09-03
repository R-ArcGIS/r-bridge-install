# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import
import os
import sys

import arcpy
import rtools
from rtools.utils import dedent


class Toolbox(object):
    def __init__(self):
        self.label = 'R Integration'
        self.alias = ''
        self.tools = [UpdateBindings, InstallBindings, RInstallDetails, RVersion]


# Tool implementation code
class UpdateBindings(object):

    def __init__(self):
        self.label = 'Update R bindings'
        self.description = dedent("""
            Update the package that ArcGIS uses to communicate with R.
            Checks with the server for any newer releases, and if
            they exist, installs the new release.""")
        self.canRunInBackground = False

    def getParameterInfo(self):
        return []

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        rtools.update_package()


class RVersion(object):
    def __init__(self):
        self.label = 'Print R Version'
        self.description = dedent("""\
            Print the version of R that ArcGIS is connected to.""")
        self.canRunInBackground = False

    def getParameterInfo(self):
        return []

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        rtools.r_version()


class RInstallDetails(object):
    def __init__(self):
        self.label = 'R Installation Details'
        self.description = dedent("""\
            Show details of R installation. Also detects
            the presence of the ArcGIS R bridge, if installed.
            """)
        self.canRunInBackground = False

    def getParameterInfo(self):
        return []

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        if rtools.r_install_path is None:
            arcpy.AddError(dedent("""\
                R not installed. Please install R prior to using
                this toolbox. The R installation can be found at:
                  http://www.r-project.org/
                """))
        else:
            arcpy.AddMessage("R (version {}), installed in: {}".format(
                rtools.r_version_info, rtools.r_install_path))
            arcpy.AddMessage("R packages will be installed into: {}".format(
                rtools.r_library_path))

            current_package_path = rtools.rpath.r_pkg_path()
            current_package_version = rtools.rpath.r_pkg_version()
            if current_package_path is None or current_package_version is None:
                arcpy.AddWarning(dedent("""\
                    The ArcGIS R package is not installed. Use the 'Install
                    R Bindings' tool to install them."""))
            else:
                arcpy.AddMessage(
                    "The ArcGIS R package (version {}) is installed at: {}".format(
                        rtools.rpath.r_pkg_version(), current_package_path))


class InstallBindings(object):

    def __init__(self):
        self.label = 'Install R bindings'
        self.description = dedent("""\
            Install ArcGIS R bindings onto this machine. R must first
            be installed for this command to correctly function.""")
        self.canRunInBackground = False

    def getParameterInfo(self):
        # overwrite existing?
        param_1 = arcpy.Parameter()
        param_1.name = 'overwrite'
        param_1.displayName = 'Overwrite Existing Installation?'
        param_1.parameterType = 'Required'
        param_1.direction = 'Input'
        param_1.datatype = 'GPBoolean'
        param_1.value = False

        return [param_1]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        rtools.install_package(overwrite=parameters[0].value)
