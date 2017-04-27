#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Mon Apr 17 11:29:56 2017
Last updated on Tue Apr 25, 2017
@author: dzelenak

1.  Iterate through the Segment Length rasters (SegLength_YYYY.tif)
2.  For each raster, convert the file to a numpy array group 
    the resulting values into classes that can have a color map applied.
3.  Write the array back to a raster file 

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

    templist = glob.glob("{a}/{b}*.tif".format( a=infolder , b=pattern))

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
        outarray = the input numpy array with modified values
    """

    inarray[ (inarray == 0) ] = 0
    inarray[ (inarray > 0) & (inarray <= 100)] = 1
    inarray[ (inarray > 100) & (inarray <= 250) ] = 2
    inarray[ (inarray > 250) & (inarray <= 500) ] = 3
    inarray[ (inarray > 500) & (inarray <= 1000) ]= 4
    inarray[ (inarray > 1000) & (inarray <= 1500) ] = 5
    inarray[ (inarray > 1500) & (inarray <= 2000) ] = 6
    inarray [ (inarray > 2000) & (inarray <= 2500) ] = 7
    inarray [ (inarray > 2500) & (inarray <= 3000) ] = 8
    inarray [ (inarray > 3000) & (inarray <= 3500) ] = 9
    inarray [ (inarray > 3500) & (inarray <= 4000) ] = 10
    inarray [ (inarray > 4000) & (inarray <= 4500) ] = 11
    inarray [ (inarray > 4500) & (inarray <= 5000) ] = 12
    inarray [ (inarray > 5000) & (inarray <= 5500) ] = 13
    inarray [ (inarray > 5500) & (inarray <= 5750) ] = 14
    inarray [ (inarray > 5750) & (inarray <= 6000) ] = 15
    inarray [ (inarray > 6000) & (inarray <= 6500) ] = 16
    inarray [ (inarray > 6500) & (inarray <= 6750) ] = 17
    inarray [ (inarray > 6750) & (inarray <= 7000) ] = 18
    inarray [ (inarray > 7000) & (inarray <= 7500) ] = 19
    inarray [ (inarray > 7500) & (inarray <= 8000) ] = 20
    inarray [ (inarray > 8000) & (inarray <= 8500) ] = 21
    inarray [ (inarray > 8500) & (inarray <= 9000) ] = 22
    inarray [ (inarray > 9000) & (inarray <= 9500) ] = 23
    inarray [ (inarray > 9500) & (inarray <= 10000) ] = 24
    inarray [ (inarray > 10000) & (inarray <= 10500) ] = 25
    inarray [ (inarray > 10500) & (inarray <= 11000) ] = 26
    inarray [ (inarray > 11000) & (inarray <= 11500) ] = 27
    inarray [ (inarray > 11500) & (inarray <= 12000) ] = 28
    inarray [ (inarray > 12000)] = 29

    outarray = inarray.astype( dtype=np.uint8 )

    return outarray

#%%
def get_outname(infile, pat):

    """Generate the output directory and filename

    Args:
        infile = the input directory
        pat = name of the product being reclassified (e.g. ChangeMagMap)
    Returns:
        outfile = the full path to the output file
    """

    indir, infile = os.path.split(infile)

    outdir = "{a}/{b}_reclass".format( a=indir, b=pat )

    outdir.replace("\\", "/")

    outname, ext = os.path.splitext(infile)

    outname = outname + "_reclass" + ext

    if not os.path.exists( outdir ): os.mkdir( outdir )

    outfile = outdir + "/" + outname

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
    outraster = driver.Create( outfile, cols, rows, 1, gdal.GDT_Byte )

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
    
    print("\n\t[-i Input File Directory]\n" \
    "\t[-from The start year]\n" \
    "\t[-to The end year]\n" \
    "\t[-help Display this message]\n\n")

    print("\n\tExample: reclassify_seglength.py -i C:/.../CCDCMap -from " + \
          "1984 -to 2015")

    print ""

    
    return None
    
#%%
def main():
    
    argv = sys.argv

    fromyear, toyear = None, None

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
    
    """# Test values
    infolder = (r"C:/...ChangeMaps")
    fromyear, toyear = "1984", "2014"
    """
    
    lookfor = "SegLength"

    rasters = get_layers(infolder, lookfor, fromyear, toyear)
    print rasters
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
