"""
Last Updated: 2/2/2017 by Dan Zelenak to work on LCSRLNST01,
2/6/2017 to compute CCDC vs NLCD land cover from-to comparison (output 32-bit raster)
8/31/2017 updating to Python 3.6
"""
# TODO make changes to work with nlcd and trends, take in name argument
import datetime
import glob
import os
import sys
import traceback

from osgeo import gdal
import numpy as np

print(sys.version)

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S"))


def allCalc(ccdcdir, refdir, outdir, name, yyyy1, yyyy2):
    try:

        # Extract last 2 digits from years to use for naming
        yy1, yy2 = yyyy1[-2:], yyyy2[-2:]

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        ccdc_list = glob.glob("{dir}{sep}{y1}_{y2}{sep}*.tif".format(dir=ccdcdir, sep=os.sep, y1=yyyy1, y2=yyyy2))

        ref_list = glob.glob(refdir + os.sep + "*.tif")

        ccdc_list.sort()

        ref_list.sort()

        ccdc_file = "{}{}ccdc{}to{}cl.tif".format(ccdcdir, os.sep, yyyy1, yyyy2)

        if not os.path.exists(ccdc_file):

            ccdc_file = "{}{}ccdc{}to{}cl.tif".format(ccdcdir, os.sep, yyyy1, yyyy2)

            if not os.path.exists(ccdc_file):
                print("Could not locate file {}, may need to compute change layers "
                      "for CCDC year {} to year {}".format(os.path.basename(ccdc_file), yyyy1, yyyy2))

                sys.exit(0)

        ref_file = "{dir}{sep}{name}{y1}to{y2}cl.tif".format(dir=refdir, sep=os.sep, name=name, y1=yyyy1, y2=yyyy2)

        if not os.path.exists(ref_file):

            ref_file = "{dir}{sep}{name}{y1}to{y2}cl.tif".format(dir=refdir, sep=os.sep, name=name, y1=yy1, y2=yy2)

            if not os.path.exists(ref_file):
                print("Could not locate file {}, may need to compute change layers "
                      "for CCDC year {} to year {}".format(os.path.basename(ref_file), yyyy1, yyyy2))

                sys.exit(0)

        out_file = '{a}{b}{name}{c}to{d}cl_ccdc{c}to{d}cl.tif'.format(a=outdir, b=os.sep, c=yyyy1, d=yyyy2, name=name)

        if not os.path.exists(out_file):

            ccdc = read_data(ccdc_file)

            ref = read_data(ref_file)

            results = np.zeros_like(ccdc["data"], dtype=np.float32)

            results = ccdc["data"] * 10000.0 + ref["data"]

            write_raster(out_file, ccdc["geo"], ccdc["prj"], ccdc["cols"], ccdc["rows"], results)

        else:

            print("\nFile {} already exists".format(os.path.basename(out_file)))

    except:

        print(traceback.format_exc())


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


def usage():
    print('\n\tUsage:python 6_ccdc_ref_cover_diff.py\n\n \
    \t[-ccdc Full path to the CCDC CoverDistMap layers]\n \
    \t[-ref Full path to the NLCD or Trends layers]\n \
    \t[-name nlcd or Trendsblock]\n\
    \t[-from From Year]\n \
    \t[-to To Year]\n \
    \t[-o Output Folder with complete path]\n\n \
    \tExample:\n\tpython 6_ccdc_nlcd_cover_diff.py -ccdc path_to_ccdc \n\t -nlcd path_to_nlcd -from 1992 -to 2001 \n \
    \t-o path_to_output\n')

    sys.exit(0)


def main():
    argv = sys.argv

    if argv is None:
        print("try -help")

        sys.exit(1)

    # Parse command line arguments.
    i = 1

    while i < len(argv):

        arg = argv[i]

        if arg == '-ccdc':

            i = i + 1

            inputCCDC = argv[i]

        elif arg == '-ref':

            i = i + 1

            inputNLCD = argv[i]

        elif arg =='-name':

            i = i + 1

            name = argv[i]

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
    allCalc(inputCCDC, inputNLCD, outputDir, name, year_1, year_2)


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
