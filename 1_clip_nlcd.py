"""
Description: Take CONUS NLCD layers and clip them to the extent of a given reference layer.
Based on script "RasterMask_reproject_resample_GDAL.py" by Devendra Dahal written on 5/12/2015
Last Updated: 1/10/2017, 2/2/2017, 9/18/2017 by Dan Zelenak
"""

import datetime
import glob
import os
import pprint
import subprocess
import sys
import argparse
from collections import namedtuple

print(sys.version)

WKT = "ard_srs.wkt"

GeoExtent = namedtuple('GeoExtent', ['x_min', 'y_max', 'x_max', 'y_min'])

CONUS_EXTENT = GeoExtent(x_min=-2565585,
                         y_min=14805,
                         x_max=2384415,
                         y_max=3314805)

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

    print('Input Ref File List:\n')

    pprint.pprint(file_list)

    for file in file_list:

        print('\tWorking on {}'.format(os.path.basename(file)))

        if not os.path.exists(args.output):
            os.makedirs(args.output)

        clip_extent = geospatial_hv(h=int(args.hv[0]), v=int(args.hv[1]))

        print('\n------------------------')

        print('Extent of the out layer:\n\t\t\t', clip_extent.y_max,
              '\n\n\t', clip_extent.x_min, '\t\t\t', clip_extent.y_min, '\n\n\t\t\t', clip_extent.x_max)

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

    print("\nAll done")


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print("\nProcessing time: " + str(tt))
