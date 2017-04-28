#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 19 14:32:45 2017

@author: dzelenak
"""
import os, sys, datetime, glob

import numpy as np

try:
    from osgeo import gdal
    #from osgeo.gdalconst import *
except ImportError:
    import gdal

print sys.version

t1 = datetime.datetime.now()
print "\nProcessing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n")

#driver = gdal.GetDriverByName("GTiff")
#driver.Register()

#%%
def get_inlayers(infolder, y1, y2):
    
    """Generate a list of the input change map layers with full paths
    
    Args:
        infolder = the directory containing the annual change map layers
        y1 = the 'from' year
        y2 = the 'to' year
        
    Returns:
        templist = the complete list of change map raster files
        rlist = the clipped list of change map raster files based on y1, y2
    """

    templist = glob.glob("{a}/ChangeMap*.tif".format( a=infolder ))
    
    if y1==None or y2==None:
        
        return templist
        
    else:
    
        ylist = [y for y in range(int(y1), int(y2)+1)]
        
        rlist = [r for y in ylist for r in templist if str(y) in r]
            
        return rlist

#%%    
def get_outlayers(inrasters, outfolder):
    
    """Generate a list of output rasters containing full paths
    
    Args:
        inrasters = list of the input rasters containing full paths
        outfolder = the full path to the output folder
    
    Return:
        rlist = list of output rasters to be created
    """
    
    rlist = []
    
    years = []    
    
    for r in range(len(inrasters)):
        
        dirx, filex = os.path.split(inrasters[r])
        
        name, ext = os.path.splitext(filex)
        
        years.append(name[-4:])
    
    
    for i in range(len(inrasters)):
        
        rlist.append("{a}/ccdc{b}to{c}ct.tif".format\
                    ( a=outfolder, b=years[0], c=years[i] ))

    return rlist

#%%
def do_calc(out_r, in_r1, in_r2):
    
    """Generate the output layers and add color ramps for the default
    from/to years (i.e. the min and max years present)
    
    Args:
        in_r = the input raster file
        out_r = the output raster file
        
    Returns:
        None
    """        

    driver = gdal.GetDriverByName("GTiff")
    
    if in_r1 == None:
        
        src2 = gdal.Open(in_r2)
    
        rows = src2.RasterYSize
        
        cols = src2.RasterXSize
        
        srcdata2 = src2.GetRasterBand(1).ReadAsArray()
    
        srcdata2[ srcdata2 > 0 ] = 1
        
        outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_Byte)
    
        if outfile is None:
            
            print ("\nCould not create image file {a}".format
                   ( a=os.path.basename(out_r) ))
            
            sys.exit(1)
            
        outband = outfile.GetRasterBand(1)
        outband.WriteArray(srcdata2, 0, 0)
        
        outband.FlushCache()
        outband.SetNoDataValue(255)
        
        outfile.SetGeoTransform( src2.GetGeoTransform() )
        outfile.SetProjection( src2.GetProjection() )
    
        src2, outfile = None, None
        
        return None
        
    else:

        src1 = gdal.Open(in_r1)
        src2 = gdal.Open(in_r2)
        
        rows = src1.RasterYSize
        
        cols = src1.RasterXSize
        
        srcdata1 = src1.GetRasterBand(1).ReadAsArray()
        srcdata2 = src2.GetRasterBand(1).ReadAsArray()
        
        srcdata2[ srcdata2 > 0 ] = 1
        
        sumdata = np.add(srcdata1, srcdata2)
        
        outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_Byte)
        
        if outfile is None:
            
            print ("\nCould not create image file {a}".format
                   ( a=os.path.basename(out_r) ))
            
            sys.exit(1)
            
        outband = outfile.GetRasterBand(1)
        outband.WriteArray(sumdata, 0, 0)
        
        outband.FlushCache()
        outband.SetNoDataValue(255)
        
        outfile.SetGeoTransform( src2.GetGeoTransform() )
        outfile.SetProjection( src2.GetProjection() )
        
        src1, src2, outfile = None, None, None
    
        return None
    
#%%
def usage():

    print("\t[-i Full path to the directory where annual CCDC "\
              "change layers are saved]\n" \
     "\t[-from The start year]\n" \
     "\t[-to The end year]\n" \
     "\t[-o Full path to the output folder]\n" \
     "\n\t*Output raster will be saved in the same format "\
     "as input raster (GTiff).\n\n")

    return None

#%%
def main():
    
    fromY, toY = None, None

    argv = sys.argv

    if len(argv) < 3:
        
        print "\n\tMissing one or more arguments:\n "
        
        usage()
        
        sys.exit(1)

    # Parse command line arguments.
    i = 1
    while i < len(argv):
        
        arg = argv[i]

        if arg == '-i':
            i           = i + 1
            inputdir        = argv[i]

        elif arg == '-from':
            i           = i + 1
            fromY      = argv[i]

        elif arg == '-to':
            i           = i + 1
            toY      = argv[i]

        elif arg == '-o':
            i           = i + 1
            outputdir      = argv[i]

        elif arg == '-help':
            usage()
            sys.exit(1)

        elif arg[:1] == ':':
            print('Unrecognized command option: %s' % arg)
            usage()
            sys.exit(1)

        i += 1
    
    inputdir = inputdir.replace("\\", "/")
    
    outputdir = outputdir.replace("\\", "/")
    
    if not os.path.exists(outputdir): os.mkdir(outputdir)

    infiles = get_inlayers(inputdir, fromY, toY)
    
    """
    index = []
    
    for j in range(len(infiles)):
        
        index.append(str(j))
    """    
    
    outfiles = get_outlayers(infiles, outputdir)
    
    for x in range(len(outfiles)):
    
        if x == 0: 
            
            do_calc(outfiles[x], None, infiles[x])
        
        elif x > 0: 
            
            do_calc(outfiles[x], outfiles[x-1], infiles[x])
    
    return None

#%%
if __name__ == '__main__':
    main()

#%%
t2 = datetime.datetime.now()
print "\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S")

tt = t2 - t1
print "Processing time: " + str(tt),"\n"