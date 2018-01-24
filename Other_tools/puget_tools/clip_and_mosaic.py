"""Get a list of all CoverPrim and SegmentChange maps, use specified tiles for Puget Sound eco-region, clip using
an eco-region level-3 boundary shapefile, merge tiles for each year."""

import datetime
import os
import subprocess
import argparse
from collections import namedtuple

WKT = "ard_srs.wkt"

GeoExtent = namedtuple('GeoExtent', ['x_min', 'y_max', 'x_max', 'y_min'])

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S"))

SHP = r"D:\LCMAP\PugetSound\Shapefile\Puget_dissolve_alberswgs84.shp"


def clip_and_mosaic(infiles, outdir, year, product):
    """

    :param infiles:
    :param outdir:
    :param year:
    :param product:
    :return:
    """
    outdir = outdir + os.sep + year

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Build the gdalwarp command
    clip_via_warp = "gdalwarp -cutline {shp} -crop_to_cutline ".format(shp=SHP)

    # Append input files to gdalwarp command
    for f in infiles:
        clip_via_warp = clip_via_warp + f + " "

    # Append output file to gdalwarp command
    clip_via_warp = clip_via_warp + outdir + os.sep + "puget_" + year + "_" + product + ".tif"

    print(clip_via_warp)

    subprocess.call(clip_via_warp, shell=True)

    return None

def main_work(indir, outdir):
    """

    :param indir:
    :param outdir:
    :return:
    """
    # List of ARD tiles
    HV_list = ['h03v01', 'h03v02', 'h03v03', 'h04v01', 'h04v02']

    # List of years
    years = [str(y) for y in range(1984, 2016)]

    products = ['SegChange', 'CoverPrim']

    for product in products:

        print(product)

        for year in years:

            print(year)

            infiles = []

            for hv in HV_list:

                temp = indir + os.sep + hv + os.sep + 'maps' + os.sep + hv + '_' + product + '_' + year + '.tif'

                infiles.append(temp)

            print(infiles)

            clip_and_mosaic(infiles, outdir, year, product)

    return None


def main():
    """

    :return:
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", dest="indir", type=str, required=True,
                        help="Full path to the directory containing the time-series mapped products")

    parser.add_argument("-o", "--output", dest="outdir", type=str, required=True,
                        help="Full path to the output location")

    args = parser.parse_args()

    main_work(**vars(args))

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print("\nProcessing time: " + str(tt))