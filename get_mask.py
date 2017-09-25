"""
Author: Dan Zelenak
Date: 9/25/2017
Purpose: Generate mask based on an input PyClass land cover and NLCD/Trends Land Cover.  The user specifies the class
values from each land cover from which to produce a combined land cover mask.
"""

import os
import argparse
import gdal
import numpy as np


def get_data(input):

    src = gdal.Open(input, gdal.GA_ReadOnly)

    src_data = src.GetRasterBand(1).ReadAsArray()

    return src_data


def get_raster(input, output, value, mask)

    driver = gdal.GetDriverByName("GTiff")

    outname = output + os.sep + value + ".tif"

    src0 = gdal.Open(input, gdal.GA_ReadOnly)

    cols = src0.RasterXSize
    rows = src0.RasterYSize

    outfile = driver.create(outname, cols, rows, 1, gdal.GDT_Byte)

    outband = outfile.GetRasterBand(1)
    outband.WriteArray(mask, 0, 0)

    outband.FlushCache()

    outfile.SetGeoTransform(src0.GetGeoTransform())
    outfile.SetProjection(src0.GetProjection())

    src0, outfile, outband = None, None, None


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--ccdc", required=True, help="Full path to the PyClass land cover .tif")

    parser.add_argument("-r", "--ref", required=True, help="Full path to the Trends/NLCD land cover .tif")

    parser.add_argument("-v", "--value", nargs=2, metavar="PyClass[0-9] Ref[NLCD/Trends class]",required=True, type=str,
                        help="Values representing the input "
                        "PyClass and Trends/NLCD target classes.  Use PyClass"
                        "value first, followed by the reference class")

    parser.add_argument("-o", "--output", required=True, help="The full path to the output folder")

    args = parser.parse_args()

    ccd_set = get_data(args.ccdc)

    ref_set = get_data(args.ref)

    combine_value = args.value[0] + args.value[1]

    combined_set = np.add(ccd_set * 100.0, ref_set)

    mask_set = combined_set[combined_set == int(combine_value)]

    get_raster(args.ccdc, args.output, args.value, mask_set)

