#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author: Dan Zelenak
Last Updated: 5/12/2017
Description:  Go through ChangeMap layers in reverse
and flag each pixel with the first year in which a change
is detected.  The resulting raster will show the last year that change
occurred for each pixel.
'''

import os, sys, datetime, glob, subprocess, re

import numpy as np

print sys.version

# GDALPath = '/usr/bin'
#GDALPath = r'C:\Users\dzelenak\Workspace\Testing\LCMAP_Tools\dist'

try:
    from osgeo import gdal
    # from osgeo.gdalconst import *
except ImportError:
    import gdal

t1 = datetime.datetime.now()
print "Processing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n")

gdal.AllRegister()
gdal.UseExceptions()

#%%
def get_infiles(infolder, y1, y2):

    """Generate a list of the input change map layers with full paths

    Args:
        infolder = the directory containing the annual change map layers
        y1 = the 'from' year
        y2 = the 'to' year

    Returns:
        templist = the complete list of change map raster files
        - or -
        rlist = the clipped list of change map raster files based on y1, y2
    """

    templist = glob.glob("{a}{b}ChangeMap*.tif".format( a=infolder, b=os.sep ))

    templist.sort(reverse=False)

    if y1==None or y2==None:

        return templist

    else:

        ylist = [y for y in range(int(y1), int(y2)+1)]

        rlist = [r for y in ylist for r in templist if str(y) in r]
        
        rlist.sort(reverse=False)

        return rlist

#%%
def do_calc(in_f, temp_f):

    """
    """
    src = gdal.Open(in_f, gdal.GA_ReadOnly)

    srcdata = src.GetRasterBand(1).ReadAsArray()

    #temp_out = srcdata

    #temp_out[temp_f == 0] = int(re.split("[_ .]", in_f)[1])

    root, fname = os.path.split(in_f)
    
    year_value = int(re.split("[_ .]", fname)[1])
    
    if temp_f == None:
        
        srcdata_holder = np.copy(srcdata)
        
        srcdata_holder[ srcdata_holder != 0] = year_value

        src = None

        return srcdata_holder

    elif temp_f != None:

        srcdata_holder = np.copy(srcdata)

        srcdata_holder[ temp_f != 0 ] = 0

        srcdata_holder[ srcdata_holder != 0 ] = year_value

        srcdata = (srcdata * 0) + temp_f + srcdata_holder

        src = None

        return srcdata

#%%
def get_outfile(inlist, from_y, to_y, outdir):

    """
    """

    years = []

    if from_y == None:

        for r in inlist:

            r = os.path.basename(r)

            years.append(re.split("[_ .]", r)[1])

        years.sort()

        from_y, to_y = years[0], years[-1]

    outname = "ccdc{a}to{b}yofc.tif".format( a=from_y[-2:], b=to_y[-2:] )

    outfile = outdir + os.sep + outname

    return outfile

#%%
def get_raster(infile, indata, out_r):

    """
    """
    in_src = gdal.Open(infile, gdal.GA_ReadOnly)

    cols = in_src.RasterXSize
    rows = in_src.RasterYSize

    driver = gdal.GetDriverByName("GTiff")
    
    outfile = driver.Create(out_r, cols, rows, 1, gdal.GDT_UInt16)
    
    if outfile is None:
            
        print ("\nCould not create image file {a}".format
                   ( a=os.path.basename(out_r) ))
            
        sys.exit(1)
            
    outband = outfile.GetRasterBand(1)
    outband.WriteArray(indata, 0, 0)
        
    outband.FlushCache()
    outband.SetNoDataValue(32767)
        
    outfile.SetGeoTransform( in_src.GetGeoTransform() )
    outfile.SetProjection( in_src.GetProjection() )
    
    in_src, outfile = None, None

    return None



#%%
def add_color_table(in_vrt, clr_table, dtype):
    
    """Write color map info to a VRT file
    
    Args:
        in_vrt = the input VRT file
        clr_table = the input color table (.txt)
        dtype = the bit depth of the original raster
    Return:
        out_vrt = the VRT with color map info written to it
    """
    
    
    color_table = open(clr_table, "r")

    (dirName, fileName) = os.path.split(in_vrt)
    (fileBase, fileExt) = os.path.splitext(fileName)

    out_vrt = r"{0}{1}zzzzz{2}_temp.vrt".format(dirName, os.sep, fileBase)

    in_txt = open(in_vrt, 'r+')
    out_txt = open(out_vrt, 'w')

    with open(in_vrt, 'r+') as in_txt, open(out_vrt, "w") as out_txt:
        
       # key is the line after which to insert the color table in the VRT
        key = '<VRTRasterBand dataType="{0}" band="1">'.format(dtype)
        
       # subkey is a line that doesn't need to be in the new VRT text
        subkey = "   <ColorInterp>Gray</ColorInterp>"
        
       # get lines in a list
        txt_read = in_txt.readlines()

        for line in txt_read:
        
            if subkey in line:
                
                  continue
            
            else:
                
                writetxt = r"{0}".format(line)
                
                out_txt.write(writetxt)

                # insert color table following keywords
                if key in line:
                
                    #print "\nFound the key!\n"
                    color_read = color_table.readlines()
                    
                    #print 'writing color table to vrt'
                    for ln in color_read:
                    
                        out_txt.write(ln)

    return out_vrt

#%%
def add_color(outdir, raster):
    
    """Add a color map to the created raster files
    
    Args:
        outdir = The full path to the output folder
        raster = The current raster being worked on
        
    Return:
        None
    """
    
    namex = os.path.basename(raster)
    name = os.path.splitext(namex)[0]
    
    if not os.path.exists(outdir + os.sep + "Color"):
        
        os.mkdir(outdir + os.sep + "Color")
    
    outfile = outdir + os.sep + "Color" + os.sep + namex
    
    clr_table = "color_yolc.txt"
    
    outcsv_file = r'%s%szzzzzz_%s_list.csv' % (outdir, os.sep, name)
        
    if os.path.isfile(outcsv_file):
        
        os.remove(outcsv_file)

    with open(outcsv_file, 'wb') as outcsv2_file:
            
        outcsv2_file.write(str(raster) + "\r\n")

    temp_vrt = '{}{}zzzz_{}.vrt'.format(outdir, os.sep, name)
    com      = 'gdalbuildvrt -q -input_file_list %s %s' \
                % (outcsv_file, temp_vrt)
    subprocess.call(com, shell=True)

    out_vrt = add_color_table(temp_vrt, clr_table, 'UInt16')
    
    runCom  = "gdal_translate -of %s -ot UInt16 -q" \
               " -stats -a_srs EPSG:5070 %s %s"\
               % ("GTiff", out_vrt, outfile)
    subprocess.call(runCom, shell=True)

    # remove the temp files used for adding the color tables
    for v in glob.glob(outdir + os.sep + "zzz*"):
    
        os.remove(v)
    
    
    return None

#%%
def usage():
    print('\nUsage:python 5_ccdc_yolc.py\n\n \
    [\t-i Full path to the directory containing the CCDC annual change layers] \n\
    [\t-frm From Year]\n \
    [\t-to To Year]\n \
    [\t-o Output Folderpath] \n \
    [\t-if input File Format (only 3 format supported: GTiff, HFA, and GRID)] \n \
    \tOutput raster will be saved in the same format as input raster.\n\n')

    return None

#%%
def main():

    fromyear, toyear = None, None

    argv = sys.argv

    if argv is None:
        sys.exit(0)

    # Parse command line arguments.
    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg == '-i':
            i           = i + 1
            inputdir        = argv[i]

        elif arg == '-frm':
            i           = i + 1
            fromyear      = argv[i]

        elif arg == '-to':
            i           = i + 1
            toyear      = argv[i]

        elif arg == '-o':
            i           = i + 1
            outputdir      = argv[i]

        elif arg == '-help':
            usage()
            sys.exit(1)

        elif arg[:1] == ':':
            print('Unrecognized command option: %s' % arg)
            usage()
            sys.exit(1)

        i += 1

    # create output directory if it doesn't already exist
    if not os.path.exists(outputdir): os.mkdir(outputdir)

    # generate list of input files including their full path
    # and clip the list to the date range if one was given
    in_files = get_infiles(inputdir, fromyear, toyear)

    # temp_holder1 = get_temp(in_files[0])

    for x in range(len(in_files)):

        print "\nProcessing file ", os.path.basename(in_files[x])
        
        if x == 0:

            yolc_data = do_calc(in_files[x], None)

            temp_holder1 = np.copy( yolc_data )

        else:

            yolc_data = do_calc(in_files[x], temp_holder1)

            temp_holder1 = np.copy( yolc_data )

    out_raster = get_outfile(in_files, fromyear, toyear, outputdir)
 
    get_raster(in_files[0], yolc_data, out_raster)

    add_color(outputdir, out_raster)

    return None

#%%
if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()
print "\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S")

tt = t2 - t1
print "Processing time: " + str(tt),"\n"
