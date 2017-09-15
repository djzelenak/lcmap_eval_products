# -*- coding: utf-8 -*-
"""
Author: Dan Zelenak
Purpose: Recode NLCD classes to match PyCCD classes

NLCD --> PyCCD Class Scheme

2001, 2006, 2011 NLCD
NLCDClass	NLCDClassName					RecodedNLCDClass	CCDCClass
11	 		Open Water						5					Open Water
12	 		Perennial Snow/Ice				7					Snow/ice
21	 		Developed, Open Space			1					Developed/urban
22	 		Developed, Low Intensity		1					Developed/urban
23	 		Developed, Medium Intensity		1					Developed/urban
24	 		Developed, High Intensity		1					Developed/urban
31	 		Barren Land (Rock/Sand/Clay)	8					Barren
41	 		Deciduous Forest				4					Tree Cover
42	 		Evergreen Forest				4					Tree Cover
43	 		Mixed Forest					4					Tree Cover
51	 		Dwarf Scrub (Alaska Only)		n/a					n/a
52	 		Shrub/Scrub						3					Grassland/shrubland
71	 		Grassland/Herbaceous			3					Grassland/shrubland
72	 		Sedge/Herbaceous				3					Grassland/shrubland
73	 		Lichens (Alaska Only)			n/a					n/a
74	 		Moss (Alaska Only)				n/a					n/a
81	 		Pasture/Hay						81*					Mixed Class
82	 		Cultivated Crops				2					Agriculture
90	 		Woody Wetlands					6					Wetland
95	 		Emergent Herbaceous Wetlands	6					Wetland

1992
NLCDClass	NLCDClassName								RecodedNLCDClass	CCDC Class
11			Open Water									5					Open Water
12			Perennial Snow/Ice							7					Snow/ice
21			Developed, Low Intensity Res.				1					Developed/urban
22			Developed, High Intensity Res.				1					Developed/urban
23			Developed, Commerical/Ind./Trans.			1					Developed/urban
31			Barren, Rock/Sand/Clay						8					Barren
32			Barren, Quarries/Strip Mines/Gravel Pits	1					Developed/urban**
33			Barren, Transitional						8					Barren
41			Deciduous Forest							4					Tree Cover
42			Evergreen Forest							4					Tree Cover
43			Mixed Forest								4					Tree Cover
51			Shrubland									3					Grass/shrub
61			Orchards/Vineyards/Other					2					Agriculture
71			Grassland/Herbaceous						3					Grass/shrub
81			Pasture/Hay									81*					Mixed Class
82			Row Crops									2					Agriculture
83			Small Grains								2					Agriculture
84			Fallow										2					Agriculture
85			Urban/Recreational Grasses					1					Developed/urban
91			Woody Wetlands								6					Wetland
92			Emergent Herbaceous Wetlands				6					Wetland

*  We'd like to keep this class separate to see how much of it falls in CCDC Agriculture and Grass/shrub
** Mining is included with the developed/urban PyCCD Class


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

gdal.UseExceptions()
gdal.AllRegister()


def recode_nlcd(indir, outdir=None):

    driver = gdal.GetDriverByName("GTiff")
    
    in_nlcd_list = glob.glob(indir + "*.img")

    if len(in_nlcd_list) == 0:

        in_nlcd_list = glob.glob(indir + "*.tif")

    if len(in_nlcd_list) == 0:

        print("Could not locate any NLCD layers in:\n{}".format(indir))

        sys.exit(0)
    
    for idx, nlcd in enumerate(in_nlcd_list):
        
        print("Working on recoding {}\n".format(os.path.basename(nlcd)))

        src = gdal.Open(nlcd, gdal.GA_ReadOnly)
        
        srcdata = src.GetRasterBand(1).ReadAsArray()
        
        holder = np.copy(srcdata)
        
        if nlcd[5:9] == "1992":

            holder[srcdata == 11] = 5
            holder[srcdata == 12] = 7
            holder[srcdata == 21] = 1
            holder[srcdata == 22] = 1
            holder[srcdata == 23] = 1
            holder[srcdata == 31] = 8
            holder[srcdata == 32] = 1
            holder[srcdata == 33] = 8
            holder[srcdata == 41] = 4
            holder[srcdata == 42] = 4
            holder[srcdata == 43] = 4
            holder[srcdata == 51] = 3
            holder[srcdata == 61] = 2
            holder[srcdata == 71] = 3
            holder[srcdata == 81] = 81
            holder[srcdata == 82] = 2
            holder[srcdata == 83] = 2
            holder[srcdata == 84] = 2
            holder[srcdata == 85] = 1
            holder[srcdata == 91] = 6
            holder[srcdata == 92] = 6

        else:

            holder[ srcdata == 11 ] = 5
            holder[ srcdata == 12 ] = 7
            holder[ srcdata == 21 ] = 1
            holder[ srcdata == 22 ] = 1
            holder[ srcdata == 23 ] = 1
            holder[ srcdata == 24 ] = 1
            holder[ srcdata == 31 ] = 8
            holder[ srcdata == 41 ] = 4
            holder[ srcdata == 42 ] = 4
            holder[ srcdata == 43 ] = 4
            holder[ srcdata == 51 ] = 0
            holder[ srcdata == 52 ] = 3
            holder[ srcdata == 71 ] = 3
            holder[ srcdata == 72 ] = 3
            holder[ srcdata == 73 ] = 0
            holder[ srcdata == 74 ] = 0
            holder[ srcdata == 81 ] = 81
            holder[ srcdata == 82 ] = 2
            holder[ srcdata == 90 ] = 6
            holder[ srcdata == 95 ] = 6

        
        root, file = os.path.split(nlcd)
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
    
    # in_trends_dir = r"Z:\working\ReferenceLayers\Reference_Data\TrendsMosaics\Era"

    # out_trends_dir = r"Z:\working\ReferenceLayers\Reference_Data\TrendsMosaics\Era\PyCCD_class"
    
    in_nlcd_dir = args.input
    
    out_nlcd_dir = args.output
    
    recode_nlcd(in_nlcd_dir, out_nlcd_dir)
    
if __name__ == '__main__':
    
    main()
    
t2 = datetime.datetime.now()

print (t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print ("\tProcessing time: " + str(tt))
