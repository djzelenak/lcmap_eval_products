#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Mon Apr 17 11:29:56 2017
Last updated on Tue Apr 25, 2017
@author: dzelenak

1.  Iterate through the Time Since Last Change rasters (LastChange_YYYY.tif)
2.  For each raster, convert the file to a numpy array and convert the value
    from days to years by dividing the entire array by 365 or 366.
3.  Write the array back to a raster file 

Note:  No reclassifying done in this script.  Name 'reclassify' groups this
       with other similar scripts that are used for preparing pyccd products.
"""

import os, sys, glob, datetime
import numpy as np

try:
    from osgeo import gdal
    #from osgeo.gdalconst import *
except ImportError:
    import gdal

gdal.UseExceptions()
gdal.AllRegister()

t1 = datetime.datetime.now()
print t1.strftime("\n%Y-%m-%d %H:%M:%S\n\n")

#%%
def get_layers(infolder, pattern, y1, y2):

    """Generate a list of the input layers with full paths

    Args:
        infolder = the directory containing the annual change map layers
        pattern = the product name to match (e.g. ChangeMagMap)
        y1 = the 'from' year
        y2 = the 'to' year

    Returns:
        templist = the complete list of change map raster files
        rlist = the clipped list of change map raster files based on y1, y2
    """

    templist = glob.glob("{a}{b}{c}*.tif".format
                         ( a=infolder, b=os.sep, c=pattern))

    if y1==None or y2==None:

        return templist

    else:

        ylist = [y for y in range(int(y1), int(y2)+1)]

        rlist = [r for y in ylist for r in templist if str(y) in r]

        return rlist

#%%
def get_array(inrast):

    """Open the input raster and write it to a numpy array

    Args:
        inrast = the input raster to be opened

    Returns:
        outarray = the written numpy array
    """

    tempsrc = gdal.Open(inrast)

    if tempsrc is None:

        print ("Could not open image file {a}".format
        ( a=os.path.basename(inrast) ))

        sys.exit(1)

    outarray = tempsrc.GetRasterBand(1).ReadAsArray()

    tempsrc = None

    return outarray

#%%
def array_calc(inarray):

    """Bin the array values

    Args:
        inarray = the input numpy array

    Returns:
        inarray = the input numpy array with modified values
    """

    inarray = inarray.astype( dtype=np.float32 )

    inarray = (inarray / 365.0) #* 100

    return inarray

#%%
def get_outname(infile, pat):

    """Gerenate the output directory and filename

    Args:
        infile = the input directory
        pat = name of the product being reclassified (e.g. ChangeMagMap)
    Returns:
        outfile = the full path to the output file
    """

    indir, infile = os.path.split(infile)

    outdir = "{a}{b}{c}_Years".format( a=indir, b=os.sep, c=pat )

    #outdir.replace("\\", "/")

    outname, ext = os.path.splitext(infile)

    outname = outname + "_years" + ext

    if not os.path.exists( outdir ): os.mkdir( outdir )

    outfile = outdir + os.sep + outname

    return outfile

#%%
def write_raster(raster, srcarray, outfile):

    """Take the reclassified numpy array and write it back to a raster file

    Args:
        raster = the original raster file
        srcarray = the input numpy array
        outfile = the full path to the output raster

    Returns:
        None
    """
    #=======================================================================
    #Do some initial gdal stuff=============================================

    src = gdal.Open(raster)

    if src is None:

        print ("Could not open image file {a}".format
        ( a=os.path.basename(raster) ))

        sys.exit(1)

    rows = src.RasterYSize
    cols = src.RasterXSize

    driver = src.GetDriver()

    #GDALDriver::Create() method requires image size,
    #num. of bands, and band type
    outraster = driver.Create( outfile, cols, rows, 1, gdal.GDT_CFloat32 )

    if outraster is None:

        print ("Could not create image file {a}".format
        ( a=os.path.basename(outfile) ))

        sys.exit(1)

    #=======================================================================
    #write numpy array to the raster========================================
    outband = outraster.GetRasterBand(1)
    outband.WriteArray(srcarray, 0, 0)

    #=======================================================================
    #save data to the disk and set the nodata value=========================
    outband.FlushCache()
    outband.SetNoDataValue(255)

    #=======================================================================
    #georeference the image and set the projection==========================
    outraster.SetGeoTransform( src.GetGeoTransform() )
    outraster.SetProjection( src.GetProjection() )

    src, outraster = None, None

    return None

#%%
def usage():
    #TODO
    
    return None

#%%
def main():

    argv = sys.argv

    if len(argv) <= 1:
        print "\n***Missing required arguments***"
        print "Try -help\n"
        sys.exit(0)

    i = 1

    while i < len(argv):
        arg = argv[i]

        if arg == "-i":
            i = i + 1
            infolder = argv[i]

        elif arg == "-from":
            i = i + 1
            fromyear = argv[i]
            
        elif arg == "-to":
            i = i + 1
            toyear = argv[i]

        elif arg == "-help":
            usage()
            sys.exit(1)

        i += 1
    
    lookfor = "LastChange"
    
    rasters = get_layers(infolder, lookfor, fromyear, toyear)

    for r in rasters:

        array = get_array(r)

        array = array_calc(array)

        output = get_outname(r, lookfor)

        if not os.path.exists(output):

            print "Processing image ", r, "\n"

            write_raster(r, array, output)

        array = None

    return None

#%%
if __name__ == "__main__":

    main()

#%%
t2 = datetime.datetime.now()
print t2.strftime("\n\n%Y-%m-%d %H:%M:%S")
tt = t2 - t1
print "\nProcessing time: " + str(tt)
