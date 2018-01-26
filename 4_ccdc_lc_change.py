#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Author: Dan Zelenak
Last Updated: 8/7/2017
Usage: Calculate the from-to class-to-class comparison between each year at a
user-specified interval and also between user-specified end-years
"""
import datetime
import glob
import os
import sys
import argparse
import numpy as np
import gdal
import re


def get_time():
    """
    Return the current time
    :return:
    """
    return datetime.datetime.now()


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
        ylist = the list of years present
    """

    templist = glob.glob("{}{}*{}*.tif".format(infolder, os.sep, name))

    templist.sort()

    if y1 == None or y2 == None:

        return templist

    else:

        ylist = [y for y in range(int(y1), int(y2) + 1, int(inty))]

        flist = [r for y in ylist for r in templist if str(y) in r]

        return flist, ylist


def get_outlayers(inrasters, outfolder):
    """Generate a list of output rasters containing full paths

    Args:
        inrasters = list of the input rasters containing full paths
        outfolder = the full path to the output folder

    Return:
        outlist = list of output rasters to be created
    """

    years = [re.search(r'\d+', os.path.basename(r)).group() for r in inrasters]

    outlist = ["{}{}ccdc{}to{}lcc.tif".format(outfolder, os.sep, years[i - 1], years[i]) \
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
                                                                os.path.basename(in_files[index + 1])))

                print("\tgenerating output file {}".format(os.path.basename(out_files[index])))

                src1 = gdal.Open(infile, gdal.GA_ReadOnly)

                src1data = src1.GetRasterBand(1).ReadAsArray()

                src2 = gdal.Open(in_files[index + 1], gdal.GA_ReadOnly)

                src2data = src2.GetRasterBand(1).ReadAsArray()

                from_to = (src1data * 10) + src2data

                outfile = driver.Create(out_files[index], cols, rows, 1, gdal.GDT_Byte)

                if outfile is None:
                    print("\nCould not create image file {a}".format
                          (a=os.path.basename(out_files[index])))

                    sys.exit(1)

                outband = outfile.GetRasterBand(1)
                outband.WriteArray(from_to, 0, 0)

                outband.FlushCache()
                # outband.SetNoDataValue(255)

                outfile.SetGeoTransform(src0.GetGeoTransform())
                outfile.SetProjection(src0.GetProjection())

            # reset this array to all zeros, possibly not necessary
            from_to = from_to * 0

            src1, src2, src1data, src2data, outfile = None, None, None, None, None

    return None


def main_work(inputdir, outputdir, name, y1, y2, interval=None):
    """

    :param inputdir:
    :param outputdir:
    :param name:
    :param y1:
    :param y2:
    :param interval:
    :return:
    """
    if not os.path.exists(outputdir):
        os.mkdir(outputdir)

    # create a new subdirectory based on the "from" and "to" years
    # to keep the output from/to sets organized
    outputdir = outputdir + os.sep + "{a}_{b}".format(a=y1, b=y2)

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    if interval is None:
        interval = int(y2) - int(y1)

    infiles = get_inlayers(inputdir, name, y1, y2, interval)

    outfiles, years = get_outlayers(infiles, outputdir)

    do_calc(infiles, outfiles)

    return None


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('-i', dest='inputdir', type=str, required=True,
                        help='The full path to the input directory containing annual land cover rasters')

    parser.add_argument('-o', dest='outputdir', type=str, required=True,
                        help='The full path to the output directory')

    parser.add_argument('-n', '--name', dest='name', type=str, required=True, choices=['CoverPrim', 'CoverSec'],
                        help='Specify either primary or seconday land cover')

    parser.add_argument('-y1', dest='y1', type=str, required=True,
                        help='Specify year 1 of the land cover change')

    parser.add_argument('-y2', dest='y2', type=str, required=True,
                        help='Specify year 2 of the land cover change')

    parser.add_argument('-int', dest='interval', type=int, required=False,
                        help='Specify the year interval between years 1 and 2.  The default will be year 2 - year 1.')

    args = parser.parse_args()

    main_work(**vars(args))


if __name__ == '__main__':

    t1 = get_time()

    main()

    t2 = get_time()

    print("\nProcessing time: %s" % (str(t2 - t1)))
