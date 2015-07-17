Install the R ArcGIS Tools
==========================

Install and update the R ArcGIS Bridge with this Python toolbox.


Prerequisites
-------------

 - [ArcGIS 10.3.1](http://desktop.arcgis.com/en/desktop/) or [ArcGIS Pro 1.1](http://pro.arcgis.com/en/pro-app/) ([don't have it? try a 60 day trial](http://www.esri.com/software/arcgis/arcgis-for-desktop/free-trial))
 - [R Statistical Computing Software, 3.1.0 or later](http://cran.cnr.berkeley.edu/bin/windows/base/)
  + 32-bit version required for ArcMap, 64-bit version required for ArcGIS Pro (Note: the installer installs both by default).
  + 64-bit version can be used with ArcMap by installing [Background Geoprocessing](http://desktop.arcgis.com/en/desktop/latest/analyze/executing-tools/64bit-background.htm) and configuring scripts to [run in the background](http://desktop.arcgis.com/en/desktop/latest/analyze/executing-tools/foreground-and-background-processing.htm).

How to Run
----------

First, make sure you've installed an appropriate version of R, 3.1 or later. 

**ArcGIS 10.3.1**
 - In the [Catalog window](http://desktop.arcgis.com/en/desktop/latest/map/working-with-arcmap/what-is-the-catalog-window-.htm), nagivate to the folder containing the Python Toolbox, `R Integration.pyt`. _Note_: You may have to first add a folder connection to the location that you extracted the files or downloaded via Git.
 - Open the toolbox, which should look like this:

![](https://github.com/R-ArcGIS/r-bridge-install/blob/master/img/r-bridge-install-arcmap.png)
 - Run the `Install R bindings` script. You can then test that the bridge is able to see your R installation by running the `Print R Version' and `R Installation Details` tools, and running the included [sample tools](#TODO).

**ArcGIS Pro 1.1**
 - In the [Project pane](https://pro.arcgis.com/en/pro-app/help/projects/the-project-pane.htm), either navigate to a folder connection containing the Python toolbox, or right click on *Toolboxes* > *Add Toolbox* and navigate to the location of the Python toolbox.
 - Open the toolbox, which should look like this:

![](https://github.com/R-ArcGIS/r-bridge-install/blob/master/img/r-bridge-install-pro.png)
  - Run the `Install R bindings` script. You can then test that the bridge is able to see your R installation by running the `Print R Version' and `R Installation Details` tools, and running the included [sample tools](#TODO).
