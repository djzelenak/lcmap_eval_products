#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Dan Zelenak
Last Updated: 4/28/2017
Usage: Calculate the number of changes per pixel across all available 
ChangeMap layers.  Alternatively can specify a 'from' and 'to' and the script
will calculate the number of changes for each year interval within 
the given range.
"""
import datetime
import glob
import os
import subprocess
import sys
from shutil import copy2

import numpy as np

from osgeo import gdal

print(sys.version)

t1 = datetime.datetime.now()
print("\nProcessing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n"))

gdal.AllRegister()
gdal.UseExceptions()


def get_inlayers(infolder, y1, y2):
    """Generate a list of the input change map layers with full paths
    
    Args:
        infolder = the directory containing the annual change map layers
        y1 = the 'from' year
        y2 = the 'to' year
        
    Returns:
        templist = the complete list of change map raster files
        - or -
        rlist = the clipped list of change map raster files based on y1, y2
    """

    templist = glob.glob("{a}{b}*ChangeMap*.tif".format(a=infolder, b=os.sep))

    templist.sort()

    if y1 == None or y2 == None:

        return templist

    else:

        ylist = [y for y in range(int(y1), int(y2) + 1)]

        rlist = [r for y in ylist for r in templist if str(y) in r]

        return rlist


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
        name = os.path.splitext(os.path.basename(inrasters[r]))[0]

        # Get the year value from the name string
        pieces = name.split("_")

        for piece in pieces:

            if len(piece) == 4:

                try:

                    int(piece)

                    years.append(piece)

                except ValueError:

                    continue

        # years.append(name[-4:])

    for i in range(len(inrasters)):

        rlist.append("{a}{b}ccdc{c}to{d}ct.tif".format(a=outfolder, b=os.sep, c=years[0], d=years[i]))

    return rlist


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

        if np.any(srcdata2):
        
            srcdata2[srcdata2 > 0] = 1
            
        else:
            
            srcdata2 = np.zeros_like(srcdata2)

        srcdata2 = srcdata2.astype("uint8")
        
        outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_Byte)

        if outfile is None:
            print("\nCould not create image file {a}".format
                  (a=os.path.basename(out_r)))

            sys.exit(1)

        outband = outfile.GetRasterBand(1)
        outband.WriteArray(srcdata2)

        outband.FlushCache()
        # outband.SetNoDataValue(255)

        outfile.SetGeoTransform(src2.GetGeoTransform())
        outfile.SetProjection(src2.GetProjection())

        src2, outfile = None, None

        return None

    else:

        src1 = gdal.Open(in_r1)
        src2 = gdal.Open(in_r2)

        rows = src2.RasterYSize

        cols = src2.RasterXSize

        srcdata1 = src1.GetRasterBand(1).ReadAsArray()
        srcdata2 = src2.GetRasterBand(1).ReadAsArray()

        if not np.any(srcdata1):
            
            srcdata1 = np.zeros_like(srcdata1)
            
        if not np.any(srcdata2):
            
            srcdata2 = np.zeros_like(srcdata2)
            
        srcdata2[srcdata2 > 0] = 1

        sumdata = np.add(srcdata1, srcdata2)

        sumdata = sumdata.astype("uint8")
        
        outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_Byte)

        if outfile is None:
            print("\nCould not create image file {a}".format
                  (a=os.path.basename(out_r)))

            sys.exit(1)

        outband = outfile.GetRasterBand(1)
        outband.WriteArray(sumdata)

        outband.FlushCache()
        # outband.SetNoDataValue(255)

        outfile.SetGeoTransform(src2.GetGeoTransform())
        outfile.SetProjection(src2.GetProjection())

        src1, src2, outfile = None, None, None

        return None


def add_color_table(in_vrt, clr_table, dtype):
    """Write color map info to a VRT file
    
    Args:
        in_vrt = the input VRT file
        clr_table = the input color table (.txt)
        dtype = the bit depth of the original raster
    Return:
        out_vrt = the VRT with color map info written to it
    """

    color_table = open(clr_table, "r")

    (dirName, fileName) = os.path.split(in_vrt)
    (fileBase, fileExt) = os.path.splitext(fileName)

    out_vrt = r"{0}{1}zzzzz{2}_temp.vrt".format(dirName, os.sep, fileBase)

    in_txt = open(in_vrt, 'r+')
    out_txt = open(out_vrt, 'w')

    with open(in_vrt, 'r+') as in_txt, open(out_vrt, "w") as out_txt:

        # key is the line after which to insert the color table in the VRT
        key = '<VRTRasterBand dataType="{0}" band="1">'.format(dtype)

        # subkey is a line that doesn't need to be in the new VRT text
        subkey = "   <ColorInterp>Gray</ColorInterp>"

        # get lines in a list
        txt_read = in_txt.readlines()

        for line in txt_read:

            if subkey in line:

                continue

            else:

                writetxt = r"{0}".format(line)

                out_txt.write(writetxt)

                # insert color table following keywords
                if key in line:

                    # print "\nFound the key!\n"
                    color_read = color_table.readlines()

                    # print 'writing color table to vrt'
                    for ln in color_read:
                        out_txt.write(ln)

    return out_vrt


def add_color(outdir, raster):
    """Add a color map to the created raster files
    
    Args:
        outdir = The full path to the output folder
        raster = The current raster being worked on
        
    Return:
        None
    """

    namex = os.path.basename(raster)
    name = os.path.splitext(namex)[0]

    if not os.path.exists(outdir + os.sep + "color"):
        os.makedirs(outdir + os.sep + "color")

    outfile = outdir + os.sep + "color" + os.sep + namex

    clr_table = "Color_tables{}color_numchanges.txt".format(os.sep)

    outcsv_file = r'%s%szzzzzz_%s_list.csv' % (outdir, os.sep, name)

    if os.path.isfile(outcsv_file):
        os.remove(outcsv_file)

    with open(outcsv_file, 'w') as outcsv2_file:

        outcsv2_file.write(str(raster) + "\r\n")

    temp_vrt = '{}{}zzzz_{}.vrt'.format(outdir, os.sep, name)
    com = 'gdalbuildvrt -q -input_file_list %s %s' % (outcsv_file, temp_vrt)
    subprocess.call(com, shell=True)

    out_vrt = add_color_table(temp_vrt, clr_table, 'Byte')

    runCom = "gdal_translate -of %s -ot Byte -q %s %s" % ("GTiff", out_vrt, outfile)
    subprocess.call(runCom, shell=True)

    # remove the temp files used for adding the color tables
    for v in glob.glob(outdir + os.sep + "zzz*"):
        os.remove(v)

    return None


def clean_up(outdir):
    """Purpose: Remove duplicate files in the output directory, move the
    rasters with colortable added from /color to the main output directory.
    
    Args:
        outdir = string, the full path to the output directory
        
    Return:
        None
    """
    # remove the original uncolored rasters first
    rlist = glob.glob(outdir + os.sep + "*.tif")

    for r in rlist: os.remove(r)

    # copy the colored rasters to the main output directory
    nlist = glob.glob(outdir + os.sep + "color" + os.sep + "*.tif")

    for n in nlist: copy2(n, outdir)

    # remove the old copies of the colored rasters
    for n in nlist: os.remove(n)

    # remove the /color directory
    os.removedirs(outdir + os.sep + "color")

    return None


def usage():
    print("\t[-i Full path to the directory where annual CCDC"
          "change layers are saved]\n"
          "\t[-from The start year]\n"
          "\t[-to The end year]\n"
          "\t[-o Full path to the output folder]\n"
          "\n\t*Output raster will be saved in the same format "
          "as input raster (GTiff).\n\n"

          "\tExample: 5_ccdc_num_changes.py -i /.../ChangeMaps -from 1984 -to 2015"
          " -o /.../OutputFolder\n")

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
            i = i + 1
            inputdir = argv[i]

        elif arg == '-from':
            i = i + 1
            fromY = argv[i]

        elif arg == '-to':
            i = i + 1
            toY = argv[i]

        elif arg == '-o':
            i = i + 1
            outputdir = argv[i]

        elif arg == '-help':
            usage()
            sys.exit(1)

        elif arg[:1] == ':':
            print('Unrecognized command option: %s' % arg)
            usage()
            sys.exit(1)

        i += 1

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    # create a new subdirectory based on the "from" and "to" years to keep accumulated sets organized
    outputdir = outputdir + os.sep + "{a}_{b}".format(a=fromY, b=toY)

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    infiles = get_inlayers(inputdir, fromY, toY)

    outfiles = get_outlayers(infiles, outputdir)

    for x in range(len(outfiles)):

        if x == 0:

            if not os.path.exists(outfiles[x]):

                print("\nGenerating raster file {a} from: ".format(a=os.path.basename(outfiles[x])))

                print(os.path.basename(infiles[x]))

                do_calc(outfiles[x], in_r1=None, in_r2=infiles[x])

        elif x > 0:

            if not os.path.exists(outfiles[x]):

                print("\nGenerating raster file {a} from:".format(a=os.path.basename(outfiles[x])))

                print(os.path.basename(outfiles[x - 1]), " and ", os.path.basename(infiles[x]))

                do_calc(outfiles[x], outfiles[x - 1], infiles[x])

        add_color(outputdir, outfiles[x])

    clean_up(outputdir)

    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()
print("\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1
print("Processing time: " + str(tt), "\n")
