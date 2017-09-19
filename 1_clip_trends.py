#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Dan Zelenak
Based on script originally written by Dev Dahal
Last Updated 5/16/2017
"""

import datetime
import glob
import os
import pprint
import subprocess
import sys
import argparse
import re
from collections import namedtuple

from osgeo import gdal
import numpy as np

print(sys.version)

WKT = "ard_srs.wkt"

GeoExtent = namedtuple('GeoExtent', ['x_min', 'y_max', 'x_max', 'y_min'])

CONUS_EXTENT = GeoExtent(x_min=-2565585,
                         y_min=14805,
                         x_max=2384415,
                         y_max=3314805)

print(sys.version)

t1 = datetime.datetime.now()

print(t1.strftime("%Y-%m-%d %H:%M:%S"))


def geospatial_hv(h, v, loc=CONUS_EXTENT):
    """
    Geospatial extent and 30m affine for a given ARD grid location.

    :param h:
    :param v:
    :param loc:
    :return:
    """

    xmin = loc.x_min + h * 5000 * 30
    xmax = loc.x_min + h * 5000 * 30 + 5000 * 30
    ymax = loc.y_max - v * 5000 * 30
    ymin = loc.y_max - v * 5000 * 30 - 5000 * 30

    return GeoExtent(x_min=xmin, x_max=xmax, y_max=ymax, y_min=ymin)


def remove_empty(raster):
    """Open the clipped Trends rasters and delete those that are entirely
    no data.
    
    Args:
        raster (str) = path to the Trends raster being tested
    
    Returns:
        None
    """
    test = gdal.Open(raster, gdal.GA_ReadOnly)

    testband = test.GetRasterBand(1)

    testbanddata = testband.ReadAsArray()

    if not np.any(testbanddata):

        test, testband, testbanddata = None, None, None

        os.remove(raster)

        ancillary = glob.glob(raster + '*')  # remove associated files too (.aux)

        for i in ancillary:
            os.remove(i)

        print('%s is entirely no data and it has been removed' % (os.path.basename(raster)))

    allfiles = glob.glob(raster + "*")

    for anc in allfiles:
        anc_ = re.sub("era", "", anc)

        os.rename(anc, anc_)

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", type=str, required=True,
                        help="Full path to the directory containing the ancillary data products")

    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Full path to the output location")

    parser.add_argument('-hv', nargs=2, type=str, required=False, metavar=('HH (0-32)', 'VV (0-21)'),
                        help='Horizontal and vertical ARD grid identifiers.')

    args = parser.parse_args()

    file_list = sorted(glob.glob(args.input + os.sep + '*.img'))

    if len(file_list) == 0:
        file_list = sorted(glob.glob(args.input + os.sep + '*.tif'))

    if len(file_list) == 0:
        print("Couldn't find any .img or .tif files in the specified input folder")

        sys.exit(0)

    print('Input Ref File List:\n')

    pprint.pprint(file_list)

    for file in file_list:

        print('\tWorking on {}'.format(os.path.basename(file)))

        if not os.path.exists(args.output):
            os.makedirs(args.output)

        clip_extent = geospatial_hv(h=int(args.hv[0]), v=int(args.hv[1]))

        print('\n------------------------')

        print('Extent of the out layer:\n\t\t\t', clip_extent.y_max,
              '\n\n\t', clip_extent.x_min, '\t\t\t', clip_extent.x_max, '\n\n\t\t\t', clip_extent.y_min)

        print('------------------------\n')

        in_file = os.path.basename(file)
        out_name = os.path.splitext(in_file)[0]
        out_file = args.output + os.sep + out_name + ".tif"

        print('\tProducing output {}'.format(out_file))

        run_trans = "gdal_translate -projwin {ulx} {uly} {lrx} {lry} -a_srs {wkt} {src} {dst}".format(
            ulx=clip_extent.x_min, uly=clip_extent.y_max,
            lrx=clip_extent.x_max, lry=clip_extent.y_min,
            wkt=WKT,
            src=file,
            dst=out_file)

        subprocess.call(run_trans, shell=True)

        # check if dataset is empty
        remove_empty(out_file)

    print("\nAll done")

    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print("\nProcessing time: " + str(tt))
