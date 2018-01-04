"""
Author: Dan Zelenak
Date: 9/25/2017
Purpose: Generate mask based on an input PyClass land cover and NLCD/Trends Land Cover.  The user specifies the class
values from each land cover from which to produce a combined land cover mask.
"""

import os
import sys
import argparse
import numpy as np
from osgeo import gdal


def err_mesg(src):
    """

    :return:
    """
    print(f"Error opening file {src}")

    sys.exit(1)


def get_data(input):
    """

    :param input: <str>
    :return: <numpy.ndarray>
    """
    src = gdal.Open(input, gdal.GA_ReadOnly)

    if src is None:
        err_mesg(src=src)

    return src.GetRasterBand(1).ReadAsArray()


def get_raster(ref1, ref2, out_dir, value, mask):
    """

    :param ref1: <str>
    :param ref2: <str>
    :param out_dir: <str>
    :param value: <str>
    :param mask: <numpy.ndarray>
    :return:
    """
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    driver = gdal.GetDriverByName("GTiff")

    basename1 = os.path.splitext(os.path.basename(ref1))[0]

    basename2 = os.path.splitext(os.path.basename(ref2))[0]

    outname = f"{out_dir}{os.sep}{basename1}_{basename2}_{value}.tif"

    src0 = gdal.Open(ref1, gdal.GA_ReadOnly)

    if src0 is None:
        err_mesg(src=src0)

    cols = src0.RasterXSize
    rows = src0.RasterYSize

    outfile = driver.Create(outname, cols, rows, 1, gdal.GDT_Byte)

    if outfile is None:
        err_mesg(src=outfile)

    outband = outfile.GetRasterBand(1)
    outband.WriteArray(mask, 0, 0)

    outfile.SetGeoTransform(src0.GetGeoTransform())
    outfile.SetProjection(src0.GetProjection())

    src0, outfile, outband = None, None, None

    return None


def main_work(input1, input2, values, output):
    """

    :param input1: <str>
    :param input2: <str>
    :param values: <int, list>
    :param output: <str>
    :return:
    """
    set1 = get_data(input1)

    set2 = get_data(input2)

    conc_value = values[0] * 100 + values[1]

    combined_set = np.add(set1 * 100.0, set2)

    mask_set = np.zeros_like(combined_set)

    mask_set[combined_set == conc_value] = 1

    get_raster(input1, input2, output, str(conc_value), mask_set)

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-f1", dest="input1", required=True, type=str,
                        help="Full path to the first input land cover TIFF")

    parser.add_argument("-f2", dest="input2", required=True, type=str,
                        help="Full path to the second input land cover TIFF")

    parser.add_argument("-v", "--value", dest="values", nargs=2, metavar=("PyClass[0-9]", "Ref[any value present in the ref dataset]"),
                        required=True,
                        type=int, help="Values representing the input "
                        "target classes.  Use input1"
                        "class value first, followed by the input2 class value")

    parser.add_argument("-o", dest="output", required=True, type=str,
                        help="The full path to the output folder")

    args = parser.parse_args()

    main_work(**vars(args))

