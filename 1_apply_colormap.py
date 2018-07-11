#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Apply a color table using the GDAL method of converting the input raster
to a VRT, inserting the color table into the VRT, and then writing it
back to a new .tif raster.  
Author: Dan Zelenak
Last Updated: 8/4/2017 by Dan Zelenak
"""

import os
import sys
import datetime
import glob
import subprocess
import argparse
import ast

from osgeo import gdal

t1 = datetime.datetime.now()
print("\n", t1.strftime("%Y-%m-%d %H:%M:%S"))


def add_color_table(in_file, clr_table, dtype):
    """Open the .txt file which contains the color table information and
    insert it into the xml code of the .vrt file

    Args:
        in_file = the vrt file produced from the original raster file
        clr_table = the color table .txt file
        dtype = the data type of the original raster file (e.g. Byte)
    Returns:
        out_vrt = the edited vrt file containing color table information
    """

    clr_table = "Color_tables%s%s" % (os.sep, clr_table)

    color_table = open(clr_table, "r")

    # split the path and file name
    (dirname, filename) = os.path.split(in_file)
    (filebase, fileext) = os.path.splitext(filename)

    out_vrt = r"%s%szzzzz%s_temp.vrt" % (dirname, os.sep, filebase)

    # open the input vrt file as read-only
    txt = open(in_file, "r+")

    # get lines in a list
    txt_read = txt.readlines()

    # check text for keywords
    key = '<VRTRasterBand dataType="%s" band="1">' % (dtype)

    # create and open the output vrt file for writing
    out_txt = open(out_vrt, "w")

    for line in txt_read:

        write = r"%s" % line

        out_txt.write(write)

        # insert color table following keywords
        if key in line:

            color_read = color_table.readlines()

            for ln in color_read:
                out_txt.write(ln)

    out_txt.close()

    return out_vrt


def all_calc(infile, outputdir, outfile, clrtable, dtype):
    """Primary function that runs gdal executables.  Takes in a single input
    raster file, a specified output directory including the full path, output 
    file name with full path, as well as the appropriate color table and data 
    type of the output raster.
    
    Args:
        infile = the full path to the current input raster
        outputdir = the full path to the output folder
        outfile = the full path and name of the output raster
        clrtable = the color table to be used
        dtype = the data type of the output raster (e.g. Byte)
    Returns:
        None
    """
    outcsv_file = r"%s%szzzz_%s_list.csv" % (outputdir, os.sep, os.path.basename(infile))

    if os.path.isfile(outcsv_file):
        os.remove(outcsv_file)

    open_csv = open(outcsv_file, "wb")

    # -----------------------------------------------------------------------
    # Generate a temporary output raster file--------------------------------
    tempoutfile = outputdir + os.sep + "zzzz_" + os.path.basename(infile) + ".tif"

    runsubset = "gdal_translate -of %s -b %s -q %s %s" % ("GTiff", "1", infile, tempoutfile)

    subprocess.call(runsubset, shell=True)

    # write temporary raster file path to this .csv file (required for VRT)
    if sys.version[0] == '3':
        open_csv.write(tempoutfile.encode("utf-8") + "\r\n".encode("utf-8"))

    else:
        open_csv.write(tempoutfile + "\r\n")

    open_csv.close()

    # -----------------------------------------------------------------------
    # Genereate temporary VRT file based on temp raster listed in .csv file
    temp_VRT = outputdir + os.sep + "zzzz_" + os.path.basename(infile) + ".vrt"

    com = "gdalbuildvrt -q -input_file_list %s %s" % (outcsv_file, temp_VRT)

    subprocess.call(com, shell=True)

    # subprocess.call(com, shell=True)

    color_VRT = add_color_table(temp_VRT, clrtable, dtype)

    # -----------------------------------------------------------------------
    # Write the VRT w/ color table added to the output raster file
    runCom = "gdal_translate -of %s -q -stats %s %s" % ("GTiff", color_VRT, outfile)

    subprocess.call(runCom, shell=True)

    """
    # -----------------------------------------------------------------------
    #Add spatial reference system to output raster file
    runEdit = "%s/gdal_edit.py -a_srs EPSG:5070 %s" % (GDALpath, outfile)
    subprocess.call(runEdit, shell=True)
    """

    get_srs(infile, outfile)

    # Remove temporary files (1 each of a .csv, .vrt, and .tif)
    for v in glob.glob(outputdir + os.sep + "zzz*"):
        os.remove(v)

    return None


def get_srs(inraster, outraster):
    """Apply a spatial reference system to the new raster file based on the
    SRS of the original raster
    
    Args:
        inraster = the original input raster file
        outraster = the newly created raster file that contains a color map
    Returns:
        None
    """

    in_src = gdal.Open(inraster, gdal.GA_ReadOnly)
    out_src = gdal.Open(outraster, gdal.GA_Update)

    out_src.SetGeoTransform(in_src.GetGeoTransform())
    out_src.SetProjection(in_src.GetProjection())

    in_src = None
    out_src = None

    # build_overviews(outraster)

    return None


def build_overviews(outraster):
    """
    
    :param outraster:
    :return:
    """
    out_src = gdal.Open(outraster, gdal.GA_ReadOnly)

    out_src.BuildOverviews(resampling="NEAREST", overviewlist=[2,4,8])

    out_src = None

    return None

def main_work(indir, name, outdir, ovr):
    """

    :param indir:
    :param name:
    :param outdir:
    :return:
    """
    outputdir = "%s%s%s_color" % (outdir, os.sep, name)

    ovr = ast.literal_eval(ovr)

    filelist = sorted(glob.glob("{}{}*{}*.tif".format(indir, os.sep, name)))

    if not os.path.exists(outputdir):
        os.makedirs(outputdir)

    names = ["CoverPrim", "CoverSec", "CoverConfPrim", "CoverConfSec",
             "ChangeMap", "LastChange", "SegLength", "QAMap", "ChangeMagMap"]

    colortables = ["color_covermap.txt", "color_covermap.txt",
                   "color_coverconf.txt", "color_coverconf.txt",
                   "color_changemap.txt", "color_lastchange.txt",
                   "color_seglength.txt", "color_qa.txt",
                   "color_changemag.txt"]

    dtypes = ["Byte", "Byte", "Byte", "Byte", "UInt16",
              "Byte", "Byte", "Byte", "Byte"]

    lookupcolor = dict(zip(names, colortables))

    lookuptype = dict(zip(names, dtypes))

    clrtable = lookupcolor[name]

    dtype = lookuptype[name]

    print("\nFiles saving to {}\n".format(outputdir))

    for r in filelist:

        outfile = outputdir + os.sep + os.path.basename(r)

        file_exists = os.path.exists(outfile)

        if (file_exists and ovr) or not file_exists:

            try:
                os.remove(outfile)
            except:
                pass

            print("Processing file ", r, "\n")

            # Call the primary function
            all_calc(r, outputdir, outfile, clrtable, dtype)

        elif file_exists and not ovr:

            continue

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.usage = __doc__

    parser.add_argument('-i', '--input', dest='indir', type=str, required=True,
                        help="The full path to the input directory")

    parser.add_argument('-n', dest='name', type=str, required=True,
                        choices=["CoverPrim", "CoverSec", "CoverConfPrim", "CoverConfSec",
                                 "ChangeMap", "LastChange", "SegLength", "QAMap", "ChangeMagMap"],
                        help='Input product name')

    parser.add_argument('-o', '--output', dest='outdir', type=str, required=True,
                        help='The full path to the output directory')

    parser.add_argument('-ovr', dest='ovr', type=str, required=False, default='False',
                        help="Specify whether or not to overwrite the file if it already exists")

    args = parser.parse_args()

    main_work(**vars(args))


if __name__ == "__main__":
    main()

    t2 = datetime.datetime.now()

    print(t2.strftime("%Y-%m-%d %H:%M:%S"))

    tt = t2 - t1

    print("\nProcessing time: " + str(tt))
