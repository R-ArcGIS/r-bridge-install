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
        self.alias = 'rintegration'
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
        version = arcpy.Parameter()
        version.name = 'r_version'
        version.displayName = 'Selected R Version (Set As Default)'
        version.parameterType = 'Required'
        version.direction = 'Input'
        version.datatype = 'GPString'

        return [version]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)

        if not parameters[0].altered:
            # check the registry 'Current' version only
            if rtools.r_version(True):
                parameters[0].value = rtools.r_version(True)
                parameters[0].enabled = False
            else:
                # otherwise, pull up the list of installed versions
                # and allow the user to select one to set.
                r_versions = rtools.r_version_dict()
                parameters[0].filter.list = r_versions.keys()
        if validator:
            return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        if parameters[0].enabled:
            set_default_r(parameters[0].value)
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
        arcpy.AddMessage(rtools.r_version())


class RInstallDetails(object):
    def __init__(self):
        self.label = 'R Installation Details'
        self.description = dedent("""\
            Show details of R installation. Also detects
            the presence of the ArcGIS R bridge, if installed.
            """)
        self.canRunInBackground = False

    def getParameterInfo(self):
        # detected R installation directory
        r_install = arcpy.Parameter()
        r_install.name = 'r_install'
        r_install.displayName = 'R Installation Directory'
        r_install.parameterType = 'Derived'
        r_install.direction = 'Output'
        r_install.datatype = 'GPString'

        # detected R package library
        r_pkgs = arcpy.Parameter()
        r_pkgs.name = 'r_pkgs'
        r_pkgs.displayName = 'R Package Library'
        r_pkgs.parameterType = 'Derived'
        r_pkgs.direction = 'Output'
        r_pkgs.datatype = 'GPString'

        # binding version
        bind_ver = arcpy.Parameter()
        bind_ver.name = 'bind_ver'
        bind_ver.displayName = 'ArcGIS binding version'
        bind_ver.parameterType = 'Derived'
        bind_ver.direction = 'Output'
        bind_ver.datatype = 'GPString'

        # binding path
        bind_path = arcpy.Parameter()
        bind_path.name = 'bind_path'
        bind_path.displayName = 'ArcGIS binding path'
        bind_path.parameterType = 'Derived'
        bind_path.direction = 'Output'
        bind_path.datatype = 'GPString'

        return [r_install, r_pkgs, bind_ver, bind_path]

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
        if rtools.r_path() is None:
            arcpy.AddError(dedent("""\
                R not installed. Please install R prior to using
                this toolbox. The R installation can be found at:
                  http://www.r-project.org/
                """))
        else:
            arcpy.AddMessage("R (version {}), installed in: {}".format(
                rtools.r_version(), rtools.r_path()))
            parameters[0].value = rtools.r_path()

            arcpy.AddMessage("R packages will be installed into: {}".format(
                rtools.r_lib_path()))
            parameters[1].value = rtools.r_lib_path()

            arcpy.AddMessage("All R package libraries detected: {}".format(
                ";".join(rtools.r_all_lib_paths())))

            current_package_path = rtools.r_pkg_path()
            current_package_version = rtools.r_pkg_version()
            if current_package_path is None or current_package_version is None:
                arcpy.AddWarning("The ArcGIS R package is not installed."
                                 " Use the 'Install R Bindings' tool to "
                                 "install it.")
            else:
                arcpy.AddMessage(
                    "The ArcGIS R package (version {}) is installed at: {}".format(
                        current_package_version, current_package_path))
                parameters[2].value = current_package_version
                parameters[3].value = current_package_path


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

        param_2 = arcpy.Parameter()
        param_2.name = 'r_version'
        param_2.displayName = 'Selected R Version (Set As Default)'
        param_2.parameterType = 'Required'
        param_2.direction = 'Input'
        param_2.datatype = 'GPString'

        return [param_1, param_2]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        validator = getattr(self, 'ToolValidator', None)

        if not parameters[1].altered:
            # check the registry 'Current' version only
            if rtools.r_version(True):
                parameters[1].value = rtools.r_version(True)
                parameters[1].enabled = False
            else:
                # otherwise, pull up the list of installed versions
                # and allow the user to select one to set.
                r_versions = rtools.r_version_dict()
                if r_versions:
                    parameters[1].filter.list = r_versions.keys()
                else:
                    # can't find current version, nor recurse.
                    # R probably isn't installed.
                    parameters[1].value = 'R not detected'
                    parameters[1].enabled = False
        if validator:
            return validator(parameters).updateParameters()

    def updateMessages(self, parameters):
        validator = getattr(self, 'ToolValidator', None)
        if validator:
            return validator(parameters).updateMessages()

    def execute(self, parameters, messages):
        if parameters[1].enabled:
            set_default_r(parameters[1].value)
        rtools.install_package(overwrite=parameters[0].value)


def set_default_r(current_version):
    """If the user doesn't have a default R configured,
       they are asked to set one here in the tool. Update the related
       registry keys as needed."""

    arcpy.AddMessage("Updating default R to {}".format(current_version))

    # get the related data for the version selected
    install_path = rtools.r_version_dict()[current_version]
    if install_path:
        # insert the values into the registry
        rtools.r_set_install(install_path, current_version)
