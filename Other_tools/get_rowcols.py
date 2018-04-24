"""Return the row/col location for all target value(s) in an array"""

import os
import numpy as np
from osgeo import gdal
import time
import argparse


def timestamp() -> str:
    """
    Return the current date/time stamp
    :return:
    """
    return time.strftime("%Y%m%d-%I%M%S")


def write_csv(outdir: str, fname: str, idx: np.ndarray) -> None:
    """
    Write the input numpy array to a .csv
    :param fname: The input raster basename
    :param outdir: Full path to the output directory
    :param idx: The numpy array containing row/col values
    :return:
    """
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outfile = outdir + os.sep + "%s_row_col_%s.csv" % (os.path.splitext(os.path.basename(fname))[0],
                                                       timestamp())

    with open(outfile, "w") as f:
        for r, c in zip(idx[0], idx[-1]):
            f.write("%s, %s\n" % (r, c))

    return None


def open_raster(src: str) -> np.ndarray:
    """
    Use gdal to open the raster and load into a numpy array
    :param src: Full path to the source raster
    :return:
    """
    return gdal.Open(src, gdal.GA_ReadOnly).ReadAsArray()


def find_vals(data: np.ndarray, val: list) -> np.ndarray:
    """
    Return an len(val) x 2 array containing row and col values for the input vals
    :param data: The source numpy array
    :param val: The value(s) to look for
    :return:
    """
    return np.where(np.in1d(data.ravel(), val).reshape(data.shape))


def main_work(src_file: str, value: list, outdir: str) -> None:
    """

    :param src_file: Full path to the input raster
    :param value: Pixel value to look for (int or float)
    :param outdir: Full path to the output directory where .csv will be saved
    :return:
    """
    write_csv(outdir=outdir, fname=src_file, idx=find_vals(data=open_raster(src_file), val=value))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", dest="src_file", type=str, required=True,
                        help="The full path to the source raster file")

    parser.add_argument("-o", dest="outdir", type=str, required=True,
                        help="The full path to the output directory where .csv will be saved")

    parser.add_argument("-v", dest="value", type=float, nargs="*", required=True,
                        help="The pixel value or values to look for")

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == "__main__":
    main()
