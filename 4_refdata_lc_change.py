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
import re
import itertools
import numpy as np
import gdal


def get_time():
    """
    Return the current time
    :return:
    """
    return datetime.datetime.now()


def get_inlayers(infolder, name, years):
    """Generate a list of the input change map layers with full paths

    Args:
        infolder = <str> the directory containing the annual change map layers

        name = <str> the cover product

    Returns:

        infile1 <str> path to the year1 input NLCD
        
        infile2 <str> path to the year2 input NLCD
        
    """

    infile1, infile2 = None, None

    if name == "trends":

        name = "Trends"

    filelist = sorted(glob.glob("{}{}*.tif".format(infolder, os.sep)))

    print("\nFound files {}".format(filelist))

    if filelist is None:

        print("Could not locate any {} data in location\n\t".format(name, infolder))

        sys.exit(0)

    yearlist = [re.search(r'\d+', os.path.basename(f)).group() for f in filelist]

    print("\nFound years {}".format(yearlist))

    if years is None:

        file2file = list(itertools.combinations(filelist, 2))

        year2year = list(itertools.combinations(yearlist, 2))

        return file2file, year2year

    else:

        file2file = []

        year2year = []

        for ind, f in enumerate(filelist):

            if yearlist[ind] == years[0]:

                infile1 = f

            elif yearlist[ind] == years[1]:

                infile2 = f

        return file2file.append((infile1, infile2)), year2year.append((years[0], years[1]))


def do_calc(name, file_fromto, year_fromto, outdir):
    """
    Generate the output layers containing the from/to class comparisons
    :param name:
    :param file_fromto:
    :param year_fromto:
    :param outdir:
    :return:
    """
    driver = gdal.GetDriverByName("GTiff")

    for ind, files in enumerate(file_fromto):

        out_name = outdir + os.sep + "{}{}to{}lcc.tif".format(name, year_fromto[ind][0], year_fromto[ind][1])

        src1 = gdal.Open(files[0], gdal.GA_ReadOnly)
        src2 = gdal.Open(files[1], gdal.GA_ReadOnly)

        rows = src1.RasterYSize
        cols = src1.RasterXSize

        srcdata1 = src1.GetRasterBand(1).ReadAsArray()
        srcdata2 = src2.GetRasterBand(1).ReadAsArray()

        data1 = srcdata1.astype(np.int16)
        data2 = srcdata2.astype(np.int16)

        from_to = np.zeros_like(data1, dtype=np.int16)

        print("\nprocessing input files {} and {}".format(os.path.basename(files[0]),
                                                        os.path.basename(files[1])))

        print("\tgenerating output file {}".format(os.path.basename(out_name)))

        from_to = (data1 * 100) + data2

        outfile = driver.Create(out_name, cols, rows, 1, gdal.GDT_Int16)

        if outfile is None:
            print("\nCould not create image file {a}".format(a=os.path.basename(out_name)))

            sys.exit(1)

        outband = outfile.GetRasterBand(1)
        outband.WriteArray(from_to, 0, 0)

        outband.FlushCache()
        outband.SetNoDataValue(0)

        outfile.SetGeoTransform(src1.GetGeoTransform())
        outfile.SetProjection(src1.GetProjection())

        src1, src2, srcdata1, srcdata2, data1, data2, outfile = None, None, None, None, None, None, None

    return None


def main_work(inputdir, outputdir, name, years=None):
    """

    :param inputdir:
    :param outputdir:
    :param name:
    :param y1:
    :param y2:
    :return:
    """
    if not os.path.exists(outputdir):

        os.mkdir(outputdir)

    files_list, years_list = get_inlayers(inputdir, name, years)

    print("\nfile2file= ", files_list)

    print("\nyear2year= ", years_list)

    do_calc(name, files_list, years_list, outputdir)

    return None


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", dest='inputdir', type=str, required=True,
                        help="The full path to the input land cover products")

    parser.add_argument("-o", "--output", dest='outputdir', type=str, required=True,
                        help="The full path to the output folder")

    parser.add_argument("-n", "--name", type=str, dest='name', required=True, choices=["nlcd", "trends"],
                        help="Specify the land cover product as NLCD or Trends")

    parser.add_argument("-years", dest='years', type=str, nargs=2, required=False,
                        help="Specify Year 1 and Year 2 for the land cover comparison")

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == '__main__':

    t1 = get_time()

    main()

    t2 = get_time()

    print("\nProcessing time: %s" %(str(t2 - t1)))
