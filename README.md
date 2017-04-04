Install the R-ArcGIS Bridge
===========================

Install and update the R-ArcGIS bridge with this Python toolbox.

**NOTE**: If you encounter problems, please [create an issue](https://github.com/R-ArcGIS/r-bridge-install/issues) so that we can take a look.


Prerequisites
-------------

 - [ArcGIS 10.3.1 or later](http://desktop.arcgis.com/en/desktop/) or [ArcGIS Pro 1.1 or later](http://pro.arcgis.com/en/pro-app/) ([don't have it? try a 60 day trial](http://www.esri.com/software/arcgis/arcgis-for-desktop/free-trial))
 - [R Statistical Computing Software, 3.1.0 or later](http://cran.cnr.berkeley.edu/bin/windows/base/) ([What is R?](http://www.r-project.org/about.html))
  + 32-bit version required for ArcMap, 64-bit version required for ArcGIS Pro (Note: the installer installs both by default).
  + 64-bit version can be used with ArcGIS Pro, or with ArcMap by installing [Background Geoprocessing](http://desktop.arcgis.com/en/desktop/latest/analyze/executing-tools/64bit-background.htm) and configuring scripts to [run in the background](http://desktop.arcgis.com/en/desktop/latest/analyze/executing-tools/foreground-and-background-processing.htm). NOTE: Background Geoprocessing only allows using the bridge from ArcGIS, not from within R itself.

![](https://github.com/R-ArcGIS/r-bridge-install/blob/master/img/version-block-detailed.png)


Installation
------------

First, make sure you've installed an appropriate version of R, 3.1 or later.

If you need to install offline, follow the [offline installation instructions](#offline-installation).

The clip below shows how to download, install and verify proper installation of the bridge:

![](https://github.com/R-ArcGIS/r-bridge-install/blob/master/img/r-install-from-pyt.gif)

###ArcGIS 10.3.1+
 - In the [Catalog window](http://desktop.arcgis.com/en/desktop/latest/map/working-with-arcmap/what-is-the-catalog-window-.htm), navigate to the folder containing the Python Toolbox, `R Integration.pyt`. _Note_: You may have to first add a folder connection to the location that you extracted the files or downloaded via GitHub.
 - Open the toolbox, which should look like this:

![](https://github.com/R-ArcGIS/r-bridge-install/blob/master/img/r-bridge-install-arcmap.png)

 - Run the `Install R bindings` script. You can then test that the bridge is able to see your R installation by running the `Print R Version` and `R Installation Details` tools, and running the included [sample tools](https://github.com/R-ArcGIS/r-bridge/tree/master/src/package/inst/examples).

###ArcGIS Pro 1.1+
 - In the [Project pane](https://pro.arcgis.com/en/pro-app/help/projects/the-project-pane.htm), either navigate to a folder connection containing the Python toolbox, or right click on *Toolboxes* > *Add Toolbox* and navigate to the location of the Python toolbox.
 - Open the toolbox, which should look like this:

![](https://github.com/R-ArcGIS/r-bridge-install/blob/master/img/r-bridge-install-pro.png)

  - Run the `Install R bindings` script. You can then test that the bridge is able to see your R installation by running the `Print R Version` and `R Installation Details` tools, and running the included [sample tools](https://github.com/R-ArcGIS/r-bridge/tree/master/src/package/inst/examples).

If everything worked, you should be ready to start! See [Next Steps](#next-steps) for where to go from here. Remember, you can update the package at any time by running the 'Update R bindings' script.

###Offline Installation
 - From a machine that does have internet access:
   + [download this repository](https://github.com/R-ArcGIS/r-bridge-install/archive/master.zip).
   + download the [latest version of the arcgisbinding package](https://github.com/R-ArcGIS/r-bridge/releases/latest). As of writing, this is `arcgisbinding_1.0.0.122.zip`.
 - Copy both zip files onto the machine that you're targeting offline installation. Extract the r-bridge-install zip. Place the `arcgisbinding_1.0.0.122.zip` into the same directory as the "R Integration" Python toolbox.
 - Run the installation procedure as listed above.

###Problems Installing?
 - A few things to check :
    + All [prerequisites](#prerequisites) have been met, such as the right version of R for your platform, and a current release of ArcGIS.
    + Make sure that your user has administrator access, and try running ArcGIS as an Administrator:
     - Start ArcGIS as an administrator, by right clicking the icon, selecting 'Run as Administrator', then trying the script
     - If that doesn't work, the package directory, "arcgisbinding", that gets installed into the R folder (usually, C:\Users\<username>\Documents\R\win-library\) into the requested place, C:\Program Files (x86)\ArcGIS\Desktop\Rintegration
    + On Windows 7, [KB2533623](https://support.microsoft.com/en-us/kb/2533623) must be installed. Without this hotfix, the library will generate the error "The procedure entry point AddDllDirectory could be located".
 - The release can be manually installed into R, as shown in [this screencast](https://4326.us/R/zipinst/r%20bridge%20install%20from%20zip_player.html). Use this if you're planning on mostly working from R.
 - Still stuck? [Add an issue and we'll take a look](https://github.com/R-ArcGIS/r-bridge-install/issues). ([More about GitHub Issues](https://help.github.com/articles/about-issues/))


Next Steps
----------

Additional resources and discussion at the [R-ArcGIS project on GeoNet](https://geonet.esri.com/groups/rstats)

Want to use tools others have developed?
 - See how complex problems can be solved with R and ArcGIS in the [Sample Tools](https://github.com/R-ArcGIS/r-sample-tools), such as model-based clustering and combining parametric and non-parametric models with semiparametric regression.
 - Check out the community page for more tools _Coming Soon_

Want to develop new tools using R?
 - Develop new R-based tools using the R package `arcgisbinding`, which is described in the [package vignette](https://r-arcgis.github.io/assets/arcgisbinding-vignette.html). There are additional resources within the [bridge repository](https://github.com/R-ArcGIS/r-bridge) and the [package documentation](https://r-arcgis.github.io/assets/arcgisbinding.pdf).

Credits
-------

This toolbox depends on the R Statistical Computing Software:

> Copyright (C) 2015 The R Foundation for Statistical Computing
> R is free software and comes with ABSOLUTELY NO WARRANTY.
> See the [COPYRIGHTS](https://github.com/wch/r-source/blob/trunk/doc/COPYRIGHTS) file for details.

This toolbox depends on [`ntfsutils`](https://github.com/sid0/ntfs):
> (c) 2012 the Mozilla Foundation and others, licensed under the
> Simplified BSD License. See the [LICENSE](https://github.com/sid0/ntfs/blob/master/LICENSE) file for details.

## License
[Apache 2.0](LICENSE)
