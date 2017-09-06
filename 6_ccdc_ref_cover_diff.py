"""
Last Updated: 2/2/2017 by Dan Zelenak to work on LCSRLNST01,
2/6/2017 to compute CCDC vs NLCD land cover from-to comparison (output 32-bit raster)
8/31/2017 updating to Python 3.6
"""

import datetime
import glob
import os
import sys
import traceback

from osgeo import gdal
import numpy as np

import argparse

print (sys.version)

t1 = datetime.datetime.now()
print (t1.strftime("%Y-%m-%d %H:%M:%S"))

def allCalc(CCDCdir, Refdir, OutDir, FromY, ToY, Name):

    try:

        # Extract last 2 digits from years to use for naming
        fromY, toY = FromY[-2:], ToY[-2:]

        if not os.path.exists(OutDir):

            os.makedirs(OutDir)

        inCCDCList = glob.glob("{dir}{sep}{y1}_{y2}{sep}*.tif".format(dir=CCDCdir, sep=os.sep, y1=FromY, y2=ToY))

        inRefList = glob.glob(Refdir + os.sep + "*.tif")

        inCCDCList.sort()

        inRefList.sort()

        ccdc_file = "{dir}{sep}{y1}_{y2}{sep}ccdc{y1}to{y2}cl.tif".format(dir=CCDCdir, sep=os.sep, y1=FromY, y2=ToY)

        if not os.path.exists(ccdc_file):

            ccdc_file = "{dir}{sep}2001_2011{sep}ccdc{y1}to{y2}cl.tif".format(dir=CCDCdir, sep=os.sep, y1=FromY, y2=ToY)

        if not os.path.exists(ccdc_file):

            print ("Need to compute change layers for CCDC year {} to year {}".format(FromY, ToY))

            sys.exit(0)

        ref_file = "{dir}{sep}{name}{y1}to{y2}cl.tif".format(dir=Refdir, sep=os.sep, name=Name, y1=fromY, y2=toY)

        if not os.path.exists(ref_file):

            ref_file = "{dir}{sep}{name}{y1}to{y2}cl.tif".format(dir=Refdir, sep=os.sep, name=Name, y1=FromY, y2=ToY)

            if not os.path.exists(ref_file):

                print ("Need to compute change layers for Ref year {} to year {}".format(FromY, ToY))

                sys.exit(0)

        bandFile = '{a}{b}{name}{c}to{d}cl_ccdc{c}to{d}cl.tif'.format(a=OutDir, b=os.sep, c=fromY, d=toY, name=Name)

        if not os.path.exists(bandFile):

            ccdc = read_data(ccdc_file)

            ref = read_data(ref_file)

            results = np.zeros_like(ccdc["data"], dtype=np.float32)

            results = ccdc["data"] * 10000.0 + ref["data"]

            write_raster(bandFile, ccdc["geo"], ccdc["prj"], ccdc["cols"], ccdc["rows"], results)

        else:

            print ("\nFile {} already exists".format(os.path.basename(bandFile)))

    except:

        print (traceback.format_exc())

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

    return {"data" : src_data, "geo" : src_geo, "prj" : src_prj, "cols" : cols, "rows" : rows}

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
                        help='Full path to the CCDC LC change layers')

    parser.add_argument('-ref', '--ref', type=str, required=True,
                        help='Full path to the reference LC change layers')

    parser.add_argument('-type', '--type', type=str, choices=['nlcd', 'trends'], required=True,
                        help='Specify either nlcd or trends')

    parser.add_argument('-o', '--output', type=str, required=True,
                        help='Full path to the output folder')

    parser.add_argument('-from', '-frm', '--year1', type=str, required=True,
                        help='The beginning year')

    parser.add_argument('-to', '--year2', type=str, required=True,
                        help='The end year')

    args = parser.parse_args()

    if args.type == "trends":

        name = "Trendsblock"

    else:

        name = "nlcd"

    # Call the primary function
    allCalc(args.ccdc, args.ref, args.output, args.year1, args.year2, name)

if __name__ == '__main__':

    main()

t2 = datetime.datetime.now()

print (t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print ("\tProcessing time: " + str(tt) )
