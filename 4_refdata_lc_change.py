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
    # from osgeo.gdalconst import *
except ImportError:
    import gdal

print(sys.version)

t1 = datetime.datetime.now()
print("\nProcessing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n"))

gdal.AllRegister()
gdal.UseExceptions()


# %%
def get_inlayers(infolder, name, y1, y2):
    """Generate a list of the input change map layers with full paths

    Args:
        infolder = <str> the directory containing the annual change map layers

        name = <str> the cover product

    Returns:

        infile1 <str> path to the year1 input NLCD
        
        infile2 <str> path to the year2 input NLCD
        
    """

    infile1, infile2 = None, None

    filelist = glob.glob("{}{}{}*.tif".format(infolder, os.sep, name))

    filelist.sort()

    yearlist = [os.path.basename(y).split("_")[1][:4] for y in filelist]

    if y1 is None or y2 is None:

        y1 == "1992"

        y2 == "2006"

    for ind, f in enumerate(filelist):

        if yearlist[ind] == y1:

            infile1 = f

        elif yearlist[ind] == y2:

            infile2 = f

    return infile1, infile2

# %%
def do_calc(name, file1, file2, outdir):
    """Generate the output layers containing the from/to class comparisons

    Args:
        file1 <string> path to the year1 NLCD layer
        file2 <string> path to the year2 NLCD layer

    Returns:
        None
    """

    y1 = os.path.basename(file1).split("_")[1][:4]
    y2 = os.path.basename(file2).split("_")[1][:4]

    ofile = outdir + os.sep + "{}{}to{}cl.tif".format(name, y1, y2)

    driver = gdal.GetDriverByName("GTiff")

    src1 = gdal.Open(file1, gdal.GA_ReadOnly)
    src2 = gdal.Open(file2, gdal.GA_ReadOnly)

    rows = src1.RasterYSize
    cols = src1.RasterXSize

    srcdata1 = src1.GetRasterBand(1).ReadAsArray()
    srcdata2 = src2.GetRasterBand(1).ReadAsArray()

    data1 = srcdata1.astype(np.int16)
    data2 = srcdata2.astype(np.int16)

    from_to = np.zeros_like(data1, dtype=np.int16)

    print("processing input files {} and {}".format(os.path.basename(file1),
                                                    os.path.basename(file2)))

    print("\tgenerating output file {}".format(os.path.basename(ofile)))

    from_to = (data1 * 100) + data2

    outfile = driver.Create(ofile, cols, rows, 1, gdal.GDT_Int16)

    if outfile is None:
        print("\nCould not create image file {a}".format
              (a=os.path.basename(ofile)))

        sys.exit(1)

    outband = outfile.GetRasterBand(1)
    outband.WriteArray(from_to, 0, 0)

    outband.FlushCache()
    outband.SetNoDataValue(-9999)

    outfile.SetGeoTransform(src1.GetGeoTransform())
    outfile.SetProjection(src1.GetProjection())

    src1, src2, srcdata1, srcdata2, data1, data2, outfile = None, None, None, None, None, None, None

    return None
# %%
def usage():
    print("\t[-i Full path to the directory where reference LC data map layers are saved]\n"
          "\t[-from The start year]\n"
          "\t[-to The end year]\n"
          "\t[-name the cover map product name]\n"
          "\t**nlcd or Trendsblock are valid names (case sensitive!)**\n"
          "\t[-o Full path to the output folder]\n"
          "\n\t*Output raster will be saved in the same format "
          "as input raster (GTiff).\n\n"

          "\tExample: 4_nlcd_lc_change.py -i /.../reference_data/NLCD -from 1992 -to 2011"
          " -o /.../OutputFolder -name nlcd")

    return None
# %%
def main():

    inputdir, outputdir, fromY, toY, name = None, None, None, None, None

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

    if not os.path.exists(outputdir): os.mkdir(outputdir)

    file1, file2 = get_inlayers(inputdir, name, fromY, toY)

    do_calc(name, file1, file2, outputdir)

    return None


# %%
if __name__ == '__main__':
    main()

# %%
t2 = datetime.datetime.now()
print("\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1
print("Processing time: " + str(tt), "\n")
