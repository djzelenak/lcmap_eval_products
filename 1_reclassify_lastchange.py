#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Mon Apr 17 11:29:56 2017
Last updated on Tue Apr 25, 2017
@author: dzelenak

1.  Iterate through the Time Since Last Change rasters (LastChange_YYYY.tif)
2.  For each raster, convert the file to a numpy array and convert the value
    from days to years by dividing the entire array by 365 or 366.  Rescale
    the value by a factor of 100.  Group the resulting values into classes
    that can have a color map applied.
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
print (t1.strftime("\n%Y-%m-%d %H:%M:%S\n\n"))

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
                         ( a=infolder, b=os.sep, c=pattern ))

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

    inarray = inarray.astype( dtype=np.float32 )
    
    inarray = (inarray / 365.0) * 100.0
    
    # inarray = inarray.astype( dtype=np.uint16 )

    inarray [ (inarray == 0) ] = 0
    inarray [ (inarray > 0) & (inarray <= 100)] = 1
    inarray [ (inarray > 100) & (inarray <= 200) ] = 2
    inarray [ (inarray > 200) & (inarray <= 300) ] = 3
    inarray [ (inarray > 300) & (inarray <= 400) ]= 4
    inarray [ (inarray > 400) & (inarray <= 500) ] = 5
    inarray [ (inarray > 500) & (inarray <= 600) ] = 6
    inarray [ (inarray > 600) & (inarray <= 700) ] = 7
    inarray [ (inarray > 700) & (inarray <= 800) ] = 8
    inarray [ (inarray > 800) & (inarray <= 900) ] = 9
    inarray [ (inarray > 900) & (inarray <= 1000) ] = 10
    inarray [ (inarray > 1000) & (inarray <= 1100) ] = 11
    inarray [ (inarray > 1100) & (inarray <= 1200) ] = 12
    inarray [ (inarray > 1200) & (inarray <= 1300) ] = 13
    inarray [ (inarray > 1300) & (inarray <= 1400) ] = 14
    inarray [ (inarray > 1400) & (inarray <= 1500) ] = 15
    inarray [ (inarray > 1500) & (inarray <= 1600) ] = 16
    inarray [ (inarray > 1600) & (inarray <= 1700) ] = 17
    inarray [ (inarray > 1700) & (inarray <= 1800) ] = 18
    inarray [ (inarray > 1800) & (inarray <= 1900) ] = 19
    inarray [ (inarray > 1900) & (inarray <= 2000) ] = 20
    inarray [ (inarray > 2000) & (inarray <= 2100) ] = 21
    inarray [ (inarray > 2100) & (inarray <= 2200) ] = 22
    inarray [ (inarray > 2200) & (inarray <= 2300) ] = 23
    inarray [ (inarray > 2300) & (inarray <= 2400) ] = 24
    inarray [ (inarray > 2400) & (inarray <= 2500) ] = 25
    inarray [ (inarray > 2500) & (inarray <= 2600) ] = 26
    inarray [ (inarray > 2600) & (inarray <= 2700) ] = 27
    inarray [ (inarray > 2700) & (inarray <= 2800) ] = 28
    inarray [ (inarray > 2800) & (inarray <= 2900) ] = 29
    inarray [ (inarray > 2900) & (inarray <= 3000) ] = 30
    inarray [ (inarray > 3000) ] = 31

    outarray = inarray.astype( dtype=np.uint8 )

    return outarray

#%%
def get_outname(infile, outfolder, pat):

    """Gerenate the output directory and filename

    Args:
        infile = the input directory
        outfolder = the output directory
        pat = name of the product being reclassified (e.g. ChangeMagMap)
    Returns:
        outfile = the full path to the output file
    """
    
    # outfolder = outfolder.replace("\\", "/")
    
    outdir = "{a}{b}{c}_reclass".format( a=outfolder, b=os.sep, c=pat )

    indir, filex = os.path.split(infile)
    fname, ext = os.path.splitext(filex)

    outname = fname + "_reclass" + ext

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
    # =======================================================================
    # Do some initial gdal stuff=============================================

    src = gdal.Open(raster)

    if src is None:

        print ("Could not open image file {a}".format
        ( a=os.path.basename(raster) ))

        sys.exit(1)

    rows = src.RasterYSize
    cols = src.RasterXSize

    driver = src.GetDriver()

    # GDALDriver::Create() method requires image size,
    # num. of bands, and band type
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
    
    print("\n\t[-i Full path to the input File Directory]\n" \
    "\t[-o Full path to the output location]\n" \
    "\t[-from The start year]\n" \
    "\t[-to The end year]\n" \
    "\t[-help Display this message]\n\n")

    print("\n\tExample: reclassify_lastchange.py -i C:/.../CCDCMap -from " + \
          "1984 -to 2015")

    return None
    
#%%
def main():
    
    fromyear, toyear = None, None
    
    argv = sys.argv

    if len(argv) <= 1:
        print ("\n***Missing required arguments***")
        print ("Try -help\n")
        sys.exit(0)

    i = 1

    while i < len(argv):
        arg = argv[i]

        if arg == "-i":
            i = i + 1
            infolder = argv[i]
            
        elif arg == "-o":
            i = i + 1
            outfolder = argv[i]

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

        # pprint.pprint(array)

        output = get_outname(r, outfolder, lookfor)

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
print (t2.strftime("\n\n%Y-%m-%d %H:%M:%S"))
tt = t2 - t1
print ("\nProcessing time: " + str(tt))



