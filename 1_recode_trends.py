# -*- coding: utf-8 -*-
"""
Author: Dan Zelenak
Purpose: Recode Trends classes to match PyCCD classes

Trends --> PyCCD Class Scheme

0 --> 0      No data (insufficient data)
2,4 --> 1    Developed (includes mining)
8 --> 2      Agriculture
7 --> 3      Grassland/shrubland
6 --> 4      Tree Cover
1 --> 5      Water bodies
9 --> 6      Wetland
11 -> 7      Ice and Snow
5 --> 8      Barren
3,10 -> 9    Disturbed or transitional

"""

import os
import sys
import glob
import numpy as np
from osgeo import gdal
import datetime

import argparse

t1 = datetime.datetime.now()

print (t1.strftime("%Y-%m-%d %H:%M:%S\n")    )


def recode_trends(indir, outdir=None):

    driver = gdal.GetDriverByName("GTiff")
    
    in_trends_list = glob.glob(indir + "*.img")

    if len(in_trends_list) == 0:

        in_trends_list = glob.glob(indir + "*.tif")

    if len(in_trends_list) == 0:

        print("Could not locate any Trends data in:\n{}".format(indir))

        sys.exit(0)
    
    for idx, trends in enumerate(in_trends_list):
        
        print("Working on recoding {}\n".format(os.path.basename(trends)))

        src = gdal.Open(trends, gdal.GA_ReadOnly)
        
        srcdata = src.GetRasterBand(1).ReadAsArray()
        
        holder = np.copy(srcdata)
        
        holder[ srcdata == 1 ] = 5
        holder[ srcdata == 2 ] = 1
        holder[ srcdata == 3 ] = 9
        holder[ srcdata == 4 ] = 1
        holder[ srcdata == 5 ] = 8
        holder[ srcdata == 6 ] = 4
        holder[ srcdata == 7 ] = 3
        holder[ srcdata == 8 ] = 2
        holder[ srcdata == 9 ] = 6
        holder[ srcdata == 10 ] = 9
        holder[ srcdata == 11 ] = 7
        
        root, file = os.path.split(trends)
        fname, ext = os.path.splitext(file)
        
        rows = src.RasterYSize
        cols = src.RasterXSize
        
        if outdir is None:
        
            outdir = root + os.sep + "pyccd_recode"
        
        if not os.path.exists(outdir):
            
            os.makedirs(outdir)
        
        outname = outdir + os.sep + fname + "_recode.tif"
        
        outraster = driver.Create(outname, cols, rows, 1, gdal.GDT_Byte)
        
        print("Generating output file {}\n".format(os.path.basename(outname)))

        outband = outraster.GetRasterBand(1)
        
        outband.WriteArray(holder, 0, 0)
        
        outband.FlushCache()
        outband.SetNoDataValue(0)
        
        outraster.SetGeoTransform( src.GetGeoTransform() )
        outraster.SetProjection( src.GetProjection() )
        
        src, srcdata, holder, outraster = None, None, None, None
        
def main():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-i', '--input', type=str, required=True, 
                        help='Full path to the location of Trends datasets')
    
    parser.add_argument('-o', '--output', type=str, required=False,
                        help='Full path to the output location')
    
    args = parser.parse_args()

    in_trends_dir = args.input
    
    out_trends_dir = args.output
    
    recode_trends(in_trends_dir, out_trends_dir)
    
if __name__ == '__main__':
    
    main()
    
t2 = datetime.datetime.now()

print (t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print ("\tProcessing time: " + str(tt))
