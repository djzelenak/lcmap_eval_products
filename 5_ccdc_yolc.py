"""
Author: Dan Zelenak
Date: 3/7/2017
Description:  Go through ChangeMap layers in reverse (ie start at 2016 and work back to 1985)
and flag each pixel when the first change is detected going back through time.  The result is a single raster
that shows in which year the last detected change occurred.
"""

import datetime
import glob
import os
import pprint
import re
import subprocess
import sys
import traceback
import argparse
import numpy as np

from osgeo import gdal

print(sys.version)

t1 = datetime.datetime.now()
print("Processing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n"))


def add_color_table(in_vrt, clr_table, dtype):
    color_table = open(clr_table, 'r')

    (dirName, fileName) = os.path.split(in_vrt)

    (fileBase, fileExt) = os.path.splitext(fileName)

    out_vrt = r'{0}{1}zzzzz{2}_temp.vrt'.format(dirName, os.sep, fileBase)

    with open(in_vrt, 'r+') as in_txt, open(out_vrt, 'w') as out_txt:
        # key is the line after which to insert the color table in the new VRT text
        key = '<VRTRasterBand dataType="{0}" band="1">'.format(dtype)

        # subkey is a line that doesn't need to be in the new VRT text
        subkey = '   <ColorInterp>Gray</ColorInterp>'

        # get lines in a list
        txt_read = in_txt.readlines()

        for line in txt_read:
            if subkey in line:

                # print '\nfound the subkey to ignore\n'
                continue
            else:
                writetxt = r'{0}'.format(line)

                out_txt.write(writetxt)

                # insert color table following keywords
                if key in line:
                    # print "\nFound the key!\n"

                    color_read = color_table.readlines()

                    # print 'writing color table to vrt'

                    for ln in color_read:

                        out_txt.write(ln)

                    # print 'done writing!'
    return out_vrt


def colorize(out_dir, temp_file, out_file, from_y, to_y):

    try:
        # ##--------color_pallette---------------------
        clr_table = 'color_yolc.txt'

        outcsv_file = f'{out_dir}{os.sep}zzzzzz_{from_y[-2:]}_to_{to_y[-2:]}_list.csv'

        if os.path.isfile(outcsv_file):
            os.remove(outcsv_file)

        with open(outcsv_file, 'wb') as outcsv2_file:
            outcsv2_file.write(temp_file.encode('utf-8') + "\r\n".encode('utf-8'))

        out_VRT = f'{out_dir}{os.sep}zzzz_{from_y[-2:]}-{to_y[-2:]}.vrt'

        com = f'gdalbuildvrt -q -input_file_list {outcsv_file} {out_VRT}'
        subprocess.call(com, shell=True)

        out_vrt = add_color_table(out_VRT, clr_table, 'UInt16')

        runCom = f'gdal_translate -of GTiff -ot UInt16  -stats -q {out_vrt} {out_file}'
        subprocess.call(runCom, shell=True)

        # remove the temp files used for adding the color tables
        for v in glob.glob(out_dir + os.sep + "zzz*"):
            os.remove(v)

    except:
        print(traceback.format_exc())

        print("Unexpected error:", sys.exc_info()[0])


def get_files(in_dir):

    return sorted(glob.glob(in_dir + os.sep + "*.tif"))


def get_years(r_list):

    return sorted([re.split('[ _ .]', os.path.split(r_file)[1])[1][-4:] for r_file in r_list])


def clip_lists(r_list, y_list, year1=None, year2=None):
    if year1 is None and year2 is None:
        return r_list, y_list, y_list[0], y_list[-1]

    if year1 is None:
        year1 = y_list[0]

    if year2 is None:
        year2 = y_list[-1]

    for index, year in reversed(list(enumerate(y_list))):
        if int(year) > int(year2):
            del y_list[index]
            del r_list[index]
        if int(year) < int(year1):
            del y_list[index]
            del r_list[index]

    return r_list, y_list, year1, year2


def load_data(raster):
    # Load raster data into array
    print('loading raster {}\n'.format(raster))

    raster_data = gdal.Open(raster, gdal.GA_ReadOnly).ReadAsArray()

    return raster_data


def make_raster(in_data, in_file, out_r):
    in_src = gdal.Open(in_file, gdal.GA_ReadOnly)

    cols = in_src.RasterXSize
    rows = in_src.RasterYSize

    driver = gdal.GetDriverByName("GTiff")

    outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_UInt16)

    if outfile is None:
        print(f"\nCould not create image file {os.path.basename(out_r)}")

        sys.exit(1)

    outband = outfile.GetRasterBand(1)
    outband.WriteArray(in_data, 0, 0)

    outband.FlushCache()
    outband.SetNoDataValue(32767)

    outfile.SetGeoTransform(in_src.GetGeoTransform())
    outfile.SetProjection(in_src.GetProjection())

    in_src, outfile = None, None

    return None


def all_calc_numpy(in_dir, out_dir, year1=None, year2=None):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    r_list = get_files(in_dir=in_dir)

    y_list = get_years(r_list=r_list)

    r_list_, y_list_, y1, y2 = clip_lists(r_list, y_list, year1, year2)

    # final output raster**
    out_file = f'{out_dir}{os.sep}ccdc{y1[-2:]}to{y2[-2:]}yolc.tif'

    # temporary output raster
    temp_file = f'{out_dir}{os.sep}zzzz{y1[-2:]}to{y2[-2:]}yolc.tif'

    src_0_data = load_data(r_list_[0])

    final_data = np.zeros_like(src_0_data, dtype=np.uint16)

    for file, year in reversed(list(zip(r_list_, y_list_))):
        raster = load_data(file)

        mask = np.logical_and(raster > 0, final_data == 0)

        final_data[mask == 1] = int(year)

    if np.any(final_data):
        make_raster(final_data, r_list_[0], temp_file)

    else:
        print(traceback.format_exc())

        print("Resulting array is all zeros:", sys.exc_info()[0])

    colorize(out_dir, temp_file, out_file, y1, y2)

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", required=True, type=str,
                       help="Full path to the folder containing CCDC DOY change layers")

    parser.add_argument("-frm", "-from", "--year1", required=False, type=str, help="The start year")

    parser.add_argument("-to", "-to", "--year2", required=False, type=str, help="The end year")

    parser.add_argument("-o", "--output", required=True, type=str, help="The full path to the output folder")

    args = parser.parse_args()

    # call the primary function
    all_calc_numpy(args.input, args.output, args.year1, args.year2)


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()
print("\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1
print("Processing time: " + str(tt), "\n")
