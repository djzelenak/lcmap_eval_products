"""
Author: Dan Zelenak
Last Updated: 2/2/2017 by Dan Zelenak to work on LCSRLNST01
and 2/6/2017 to compute CCDC vs nlcd change difference (output int16)
9/5/2017 to be compatible with python 3.6

Purpose:
Compare the number of Ref (Trends or NLCD) LC changes and PyCCD spectral changes between two years
"""

import argparse
import datetime
import glob
import os
import sys
import traceback

import numpy as np
from osgeo import gdal

print(sys.version)

t1 = datetime.datetime.now()

print(t1.strftime("%Y-%m-%d %H:%M:%S"))


def allCalc(inRef, inCCDC, outDir, FromY, ToY, Name):

    try:

        if not os.path.exists(outDir):

            os.makedirs(outDir)

        inCCDCList = glob.glob("{dir}{sep}{y1}_{y2}{sep}*.tif".format(dir=inCCDC, sep=os.sep, y1=FromY, y2=ToY))

        inRefList = glob.glob(inRef + os.sep + "*.tif")

        inCCDCList.sort()
        inRefList.sort()

        # take the last two digits from the years for file naming
        frmY, toY = FromY[-2:], ToY[-2:]

        ref_file = '{dir}{sep}{name}{y1}to{y2}ct.tif'.format(dir=inRef, sep=os.sep, name=Name, y1=frmY, y2=toY)

        ccdc_file = '{dir}{sep}ccdc{y1}to{y2}ct.tif'.format(dir=inCCDC, sep=os.sep, y1=FromY, y2=ToY)

        if not os.path.exists(ref_file):

            ref_file = '{dir}{sep}{name}{y1}to{y2}ct.tif'.format(dir=inRef, sep=os.sep, name=Name, y1=FromY, y2=ToY)

        if not os.path.exists(ref_file):

            print('Layer {} does not exist'.format(os.path.basename(ref_file)))

            sys.exit(0)

        if not os.path.exists(ccdc_file):

            print('Layer {} does not exist'.format(os.path.basename(ccdc_file)))

            sys.exit(0)

        print("\n\tmatched layers are: \n", os.path.basename(ref_file),
              "\n", os.path.basename(ccdc_file), "\n")

        print('\nFiles are saving in', outDir)

        out_file = '{dir}{sep}{name}{y1}to{y2}ct_ccdc{y1}to{y2}ct.tif'.format(dir=outDir,
                                                                              sep=os.sep, name=Name, y1=frmY, y2=toY)

        if not os.path.exists(out_file):

            ref = read_data(ref_file)

            ccdc = read_data(ccdc_file)

            results = np.zeros_like(ccdc, dtype=np.int16)

            results = ccdc["data"] * 100.0 + ref["data"]

            write_raster(out_file, ccdc["geo"], ccdc["prj"], ccdc["cols"], ccdc["rows"], results)

        else:

            print("%s was already processed".format(os.path.basename(out_file)))

    except:

        print(traceback.format_exc())

    return None


def read_data(file_name):
    """

    :param file_name: <string> path to the input file
    :return: <dict>
    """

    src = gdal.Open(file_name, gdal.GA_ReadOnly)

    src_data = src.GetRasterBand(1).ReadAsArray()

    src_geo = src.GetGeoTransform()

    src_prj = src.GetProjection()

    cols = src.RasterXSize

    rows = src.RasterYSize

    return {"data": src_data, "geo": src_geo, "prj": src_prj, "cols": cols, "rows": rows}


def write_raster(file_name, geo, prj, cols, rows, out_array):
    """

    :param file_name: <str>
    :param geo: <tuple>
    :param prj: <str>
    :param cols: <int>
    :param rows: <int>
    :param out_array: <numpy.ndarray>
    :return:
    """

    driver = gdal.GetDriverByName('GTiff')

    out_file = driver.Create(file_name, cols, rows, 1, gdal.GDT_Float32)

    out_band = out_file.GetRasterBand(1)
    out_band.WriteArray(out_array, 0, 0)

    out_band.FlushCache()
    out_band.SetNoDataValue(0)

    out_file.SetGeoTransform(geo)
    out_file.SetProjection(prj)

    out_file = None

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-ccdc', '--ccdc', type=str, required=True,
                        help='Full path to the CCDC Accumulated Change layers')

    parser.add_argument('-ref', '--ref', type=str, required=True,
                        help='Full path to the reference data change count layers')

    parser.add_argument('-o', '--output', type=str, required=True,
                        help='Full path to the output folder')

    parser.add_argument('-frm', '-from', '--year1', type=str, required=True,
                        help='The beginning year')

    parser.add_argument('-to', '--year2', type=str, required=True,
                        help='The end year')

    parser.add_argument('-n', '--name', type=str, choices=['nlcd', 'trends'], required=True,
                        help='Select either trends or nlcd as the reference data')

    args = parser.parse_args()

    # call the primary function
    allCalc(args.ref, args.ccdc, args.output, args.year1, args.year2, args.name)


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
