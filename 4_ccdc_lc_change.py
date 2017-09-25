#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Dan Zelenak
Last Updated: 8/7/2017
Usage: Calculate the from-to class-to-class comparison between each year at a
user-specified interval and also between user-specified end-years
"""
import os, sys, datetime, glob

import numpy as np

try:
    from osgeo import gdal
    #from osgeo.gdalconst import *
except ImportError:
    import gdal

print(sys.version)

t1 = datetime.datetime.now()
print("\nProcessing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n"))

gdal.AllRegister()
gdal.UseExceptions()


def get_inlayers(infolder, name, y1, y2, inty):

    """Generate a list of the input change map layers with full paths

    Args:
        infolder = the directory containing the annual change map layers
        y1 = the 'from' year
        y2 = the 'to' year
        inty = the year interval
        name = the cover product

    Returns:
        templist = the complete list of change map raster files
        - or -
        flist = the clipped list of change map raster files based on y1, y2
    """

    templist = glob.glob("{}{}{}*.tif".format(infolder, os.sep, name ))

    templist.sort()

    if y1==None or y2==None:

        return templist

    else:

        ylist = [y for y in range(int(y1), int(y2)+1, int(inty))]

        flist = [r for y in ylist for r in templist if str(y) in r]
        
        return flist


def get_outlayers(inrasters, outfolder):

    """Generate a list of output rasters containing full paths

    Args:
        inrasters = list of the input rasters containing full paths
        outfolder = the full path to the output folder

    Return:
        outlist = list of output rasters to be created
    """

    years = []

    for r in range(len(inrasters)):

        dirx, filex = os.path.split(inrasters[r])

        fname, ext = os.path.splitext(filex)

        years.append(fname[-4:])

    outlist = ["{}{}ccdc{}to{}cl.tif".format(outfolder, os.sep, years[i-1], years[i])\
               for i in range(1, len(inrasters))]
    
    return outlist, years


def do_calc(in_files, out_files):

    """Generate the output layers containing the from/to class comparisons

    Args:
        in_files = the current input raster file list
        out_files = the output raster file list

    Returns:
        None
    """

    driver = gdal.GetDriverByName("GTiff")
    
    src0 = gdal.Open(in_files[0])
    
    rows = src0.RasterYSize
    cols = src0.RasterXSize
    
    srcdata0 = src0.GetRasterBand(1).ReadAsArray()
    
    from_to = np.zeros_like(srcdata0, dtype=np.int8)
        
    for index, infile in enumerate(in_files):
        
        if index < len(in_files) - 1:

            if not os.path.exists(out_files[index]):
            
                print("processing input files {} and {}".format(os.path.basename(infile), 
                      os.path.basename(in_files[index+1])))

                print("\tgenerating output file {}".format(os.path.basename(out_files[index])))
                
                src1 = gdal.Open(infile, gdal.GA_ReadOnly)
                
                src1data = src1.GetRasterBand(1).ReadAsArray()
                
                src2 = gdal.Open(in_files[index + 1], gdal.GA_ReadOnly)
                
                src2data = src2.GetRasterBand(1).ReadAsArray()
                
                from_to = (src1data * 10) + src2data
    
                outfile = driver.Create(out_files[index], cols, rows, 1, gdal.GDT_Byte)
            
                if outfile is None:
            
                    print ("\nCould not create image file {a}".format
                           ( a=os.path.basename(out_files[index]) ))
            
                    sys.exit(1)
            
                outband = outfile.GetRasterBand(1)
                outband.WriteArray(from_to, 0, 0)
            
                outband.FlushCache()
                # outband.SetNoDataValue(255)
            
                outfile.SetGeoTransform( src0.GetGeoTransform() )
                outfile.SetProjection( src0.GetProjection() )
                
            # reset this array to all zeros, possibly not necessary
            from_to = from_to * 0
            
            src1, src2, src1data, src2data, outfile = None, None, None, None, None

    return None


def usage():

    print("\t[-i Full path to the directory where annual CCDC "
              "cover map layers are saved]\n"
     "\t[-from The start year]\n"
     "\t[-to The end year]\n"
     "\t[-int the year interval]\n"
     "\t[-name the cover map product name]\n"
     "\t**CoverPrim or CoverSec are valid names**\n"
     "\t[-o Full path to the output folder]\n"
     "\n\t*Output raster will be saved in the same format "
     "as input raster (GTiff).\n\n"

     "\tExample: 4_ccdc_lc_change.py -i /.../CoverMaps -from 1984 -to 2015"
     " int 1 -o /.../OutputFolder -name CoverPrim")

    return None


def main():

    fromY, toY = None, None

    argv = sys.argv

    if len(argv) < 3:

        print("\n\tMissing one or more arguments:\n ")

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

        elif arg == '-int':
            i = i + 1
            inty = argv[i]
        
        elif arg == '-name':
            i = i + 1
            name = argv[i]

        elif arg == '-help':
            usage()
            sys.exit(1)

        elif arg[:1] == ':':
            print('Unrecognized command option: %s' % arg)
            usage()
            sys.exit(1)

        i += 1

    if not os.path.exists(outputdir):

        os.mkdir(outputdir)

    # create a new subdirectory based on the "from" and "to" years
    # to keep the output from/to sets organized
    outputdir = outputdir + os.sep + "{a}_{b}".format(a=fromY, b=toY)

    if not os.path.exists(outputdir): os.mkdir(outputdir)
    
    infiles = get_inlayers(inputdir, name, fromY, toY, inty)

    outfiles, years = get_outlayers(infiles, outputdir)

    do_calc(infiles, outfiles)

    return None


if __name__ == '__main__':

    main()


t2 = datetime.datetime.now()
print("\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1
print("Processing time: " + str(tt),"\n")