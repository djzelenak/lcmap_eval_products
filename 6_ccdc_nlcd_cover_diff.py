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

print (sys.version)

t1 = datetime.datetime.now()
print (t1.strftime("%Y-%m-%d %H:%M:%S"))

def allCalc(CCDCdir, NLCDdir, OutDir, FromY, ToY, Name):

    try:

        # Extract last 2 digits from years to use for naming
        fromY, toY = FromY[-2:], ToY[-2:]

        if not os.path.exists(OutDir):

            os.makedirs(OutDir)

        inCCDCList = glob.glob("{dir}{sep}{y1}_{y2}{sep}*.tif".format(dir=CCDCdir, sep=os.sep, y1=FromY, y2=ToY))

        inNLCDList = glob.glob(NLCDdir + os.sep + "*.tif")

        inCCDCList.sort()

        inNLCDList.sort()

        # import pprint
        # pprint.pprint (inCCDCList) #for testing
        # pprint.pprint (inNLCDList) #for testing

        ccdc_file = "{dir}{sep}{y1}_{y2}{sep}ccdc{y1}to{y2}cl.tif".format(dir=CCDCdir, sep=os.sep, y1=FromY, y2=ToY)

        if not os.path.exists(ccdc_file):

            ccdc_file = "{dir}{sep}2001_2011{sep}ccdc{y1}to{y2}cl.tif".format(dir=CCDCdir, sep=os.sep, y1=FromY, y2=ToY)

        if not os.path.exists(ccdc_file):

            print ("Need to compute change layers for CCDC year {} to year {}".format(FromY, ToY))

            sys.exit(0)

        nlcd_file = "{}{}nlcd{}to{}cl.tif".format(NLCDdir, os.sep, fromY, toY)

        if not os.path.exists(nlcd_file):

            nlcd_file = "{}{}nlcd{}to{}cl.tif".format(NLCDdir, os.sep, FromY, ToY)

            if not os.path.exists(nlcd_file):

                print ("Need to compute change layers for {} year {} to year {}".format(Name, FromY, ToY))

                sys.exit(0)

        bandFile = '{a}{b}nlcd{c}to{d}cl_ccdc{c}to{d}cl.tif'.format(a=OutDir, b=os.sep, c=fromY, d=toY)

        if not os.path.exists(bandFile):

            ccdc = read_data(ccdc_file)
            nlcd = read_data(nlcd_file)

            results = np.zeros_like(ccdc["data"], dtype=np.float32)

            results = ccdc["data"] * 10000.0 + nlcd["data"]

            write_raster(bandFile, ccdc["geo"], ccdc["prj"], ccdc["cols"], ccdc["rows"], results)



            # Only process if the output file doesn't already exist
            # The first 3 or 4 digits are NLCD classes, last 4 digits are CCDC classes
            # runCalc  = 'gdal_calc --format GTiff --type {type} -A {file_A} -B {file_B} --outfile {outfile} --calc="(A * 10000.0 + B)" '\
                # .format(type='Int32', file_A=nlcd_file, file_B=ccdc_file, outfile=bandFile)

            # subprocess.call(runCalc, shell=True)

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


def usage():

    print('\n\tUsage:python 6_ccdc_nlcd_cover_diff.py\n\n \
    \t[-ccdc Full path to the CCDC CoverDistMap layers]\n \
    \t[-nlcd Full path to the NLCD layers]\n\
    \t[-from From Year]\n \
    \t[-to To Year]\n \
    \t[-o Output Folder with complete path]\n\n \
    \tExample:\n\tpython 6_ccdc_nlcd_cover_diff.py -ccdc path_to_ccdc \n\t -nlcd path_to_nlcd -from 1992 -to 2001 \n \
    \t-o path_to_output\n')
    
    sys.exit(0)

def main():

    argv = sys.argv

    if argv is None:

        print ("try -help")

        sys.exit(1)

    # Parse command line arguments.
    i = 1

    while i < len(argv):

        arg = argv[i]

        if arg == '-ccdc':

            i = i + 1

            inputCCDC = argv[i]

        elif arg == '-nlcd':

            i = i + 1

            inputNLCD = argv[i]

        elif arg == '-o':

            i = i + 1

            outputDir = argv[i]

        elif arg == '-from':

            i = i + 1

            fromY = argv[i]

        elif arg == '-to':

            i = i + 1

            toY = argv[i]

        elif arg == '-help':

            i = i + 1

            usage()

        i += 1

    # Call the primary function
    allCalc(inputCCDC, inputNLCD, outputDir, fromY, toY)

if __name__ == '__main__':

    main()

t2 = datetime.datetime.now()

print (t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print ("\tProcessing time: " + str(tt) )
