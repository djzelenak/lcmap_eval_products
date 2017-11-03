
"""Create a new raster that holds the concatenated QA + Cover map values for each pixel"""

import argparse
import glob
import os
import sys

import numpy as np
from osgeo import gdal


def get_file(infolder, year=None):
    """
    Return the full path of the raster file within the input folder that matches year
    :param infolder:
    :return:
    """
    if not year is None:
        return glob.glob(f"{infolder}{os.sep}*{year}.tif")
    else:
        return glob.glob(f"{infolder}{os.sep}*.tif")


def get_data(infile):
    """
    Use gdal to open the raster and return a numpy array
    :param infile:
    :return:
    """
    src = gdal.Open(infile, gdal.GA_ReadOnly)

    srcdata = src.GetRasterBand(1).ReadAsArray()

    return srcdata.astype(dtype=np.uint16)


def compute_outdata(in_qa, in_cover):
    """
    Concatenate the two input arrays
    :param in_qa:
    :param in_cover:
    :return:
    """
    out_array = np.zeros_like(in_qa, dtype=np.uint16)

    out_array = (in_qa * 100) + in_cover

    return out_array


def make_raster(in_file, out_data, outfolder):
    """
    Create the output raster containing the concatenated values
    :param outfolder:
    :param out_data:
    :return:
    """
    in_src = gdal.Open(in_file, gdal.GA_ReadOnly)

    cols = in_src.RasterXSize
    rows = in_src.RasterYSize

    driver = gdal.GetDriverByName("GTiff")

    year = in_file[-8:-4]

    out_r = f"{outfolder}{os.sep}QA_Cover{year}.tif"

    outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_UInt16)

    if outfile is None:
        print(f"\nCould not create image file {os.path.basename(out_r)}")

        sys.exit(1)

    outband = outfile.GetRasterBand(1)
    outband.WriteArray(out_data, 0, 0)

    outband.FlushCache()
    # outband.SetNoDataValue(32767)

    outfile.SetGeoTransform(in_src.GetGeoTransform())
    outfile.SetProjection(in_src.GetProjection())

    in_src, outfile = None, None

    return None


def main_work(qafolder, coverfolder, outfolder, year=None):
    """
    Concatenate the pixel values from QA and Cover maps
    :param qafolder:
    :param coverfolder:
    :param year:
    :param outfolder:
    :return:
    """
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)

    in_qa = get_file(qafolder, year)
    in_cover = get_file(coverfolder, year)

    for qa, cover in zip(in_qa, in_cover):

        qa_data = get_data(qa)
        cover_data = get_data(cover)

        out_data = compute_outdata(qa_data, cover_data)

        make_raster(cover, out_data, outfolder)


def main():
    """
    Parse the command line arguments and pass them to the main_work function
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "-qa", "--qa", type=str, required=True, help="Folder containing all QA maps")

    parser.add_argument("-c", "--cover", type=str, required=True, help="Folder containing all Cover maps")

    parser.add_argument("-o", "--output", type=str, required=True, help="Output directory")

    parser.add_argument("-y", "--year", type=str, required=False, default=None,
                        help="The target year for comparing QA and Cover maps.  "
                             "If no year is supplied, then all available years will be processed.")

    args = parser.parse_args()

    main_work(args.qa, args.cover, args.output, args.year)


if __name__ == "__main__":
    main()
