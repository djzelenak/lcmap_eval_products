"""Get a list of all CoverPrim and SegmentChange maps, use specified tiles for Puget Sound eco-region, clip using
an eco-region level-3 boundary shapefile, merge tiles for each year."""

import datetime
import os
import glob
import subprocess
import argparse
from collections import namedtuple

WKT = "ard_srs.wkt"

GeoExtent = namedtuple('GeoExtent', ['x_min', 'y_max', 'x_max', 'y_min'])

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S"))

SHP = r"D:\LCMAP\PugetSound\Shapefile\Puget_dissolve_alberswgs84_edit.shp"


def main_work(indir, outdir):
    """

    :param indir:
    :param outdir:
    :return:
    """
    filelist = glob.glob(indir + os.sep + "*.tif")

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for f in filelist:
        outfile = outdir + os.sep + os.path.basename(f)

        clip = "gdalwarp -cutline {shp} -crop_to_cutline {input} {output}".format(shp=SHP, input=f, output=outfile)

        subprocess.call(clip, shell=True)

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


if __name__ == "__main__":
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print("\nProcessing time: " + str(tt))