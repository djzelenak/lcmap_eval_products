#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Apply a color table using the GDAL method of converting the input raster
to a VRT, inserting the color table into the VRT, and finally writing it
back to a new .tif raster.  
Author: Dan Zelenak
Last Updated: 4/27/2017 by Dan Zelenak
"""

#%%
import os, sys, datetime, glob, subprocess

try:
    from osgeo import gdal
except ImportError:
    import gdal

print sys.version

t1 = datetime.datetime.now()
print "\n", t1.strftime("%Y-%m-%d %H:%M:%S")

GDALpath = "/usr/bin"
#GDALpath = "C:/LCMAP_Tools/dist"


gdal.UseExceptions()
gdal.AllRegister()

#%%
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

    color_table = open(clr_table, "r")

    # split the path and file name
    (dirname, filename) = os.path.split(in_file)
    (filebase, fileext) = os.path.splitext(filename)

    out_vrt = r"%s/zzzzz%s_temp.vrt" % (dirname, filebase)

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

#%%
def allCalc(infile, outputdir, outfile, clrtable, dtype):

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

    outcsv_file = r"%s/zzzz_%s_list.csv" \
                    % (outputdir, os.path.basename(infile))

    if os.path.isfile(outcsv_file):

        os.remove(outcsv_file)

    open_csv = open(outcsv_file, "wb")

    #-----------------------------------------------------------------------
    #Generate a temporary output raster file--------------------------------
    tempoutfile = outputdir + os.sep + "zzzz_" + \
                   os.path.basename(infile) + ".tif"
    runsubset   = "%s/gdal_translate -of %s -b %s -q %s %s"\
                   % (GDALpath, "GTiff", "1", infile, tempoutfile)
    subprocess.call(runsubset, shell=True)

    #write temporary raster file path to this .csv file (required for VRT)
    open_csv.write(str(tempoutfile) + "\r\n")

    open_csv.close()

    #-----------------------------------------------------------------------
    #Genereate temporary VRT file based on temp raster listed in .csv file
    temp_VRT =  outputdir + os.sep +  "zzzz_" + \
                os.path.basename(infile) + ".vrt"
    com      = "%s/gdalbuildvrt -q -input_file_list %s %s"\
                % (GDALpath, outcsv_file, temp_VRT)
    subprocess.call(com, shell=True)

    #subprocess.call(com, shell=True)

    color_VRT = add_color_table(temp_VRT, clrtable, dtype)

    #-----------------------------------------------------------------------
    #Write the VRT w/ color table added to the output raster file
    runCom  = "%s/gdal_translate -of %s -q %s %s"\
               % (GDALpath, "GTiff", color_VRT, outfile)
    subprocess.call(runCom, shell=True)

    """
    #-----------------------------------------------------------------------
    #Add spatial reference system to output raster file
    runEdit = "%s/gdal_edit.py -a_srs EPSG:5070 %s"\
               %(GDALpath, outfile)
    subprocess.call(runEdit, shell=True)
    """
    
    get_srs(infile, outfile)
        
        
    
    #Remove temporary files (1 each of a .csv, .vrt, and .tif)
    for v in glob.glob(outputdir + os.sep+ "zzz*"):

        os.remove(v)

    return None

#%%
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
    
    out_src.SetGeoTransform( in_src.GetGeoTransform() )
    out_src.SetProjection( in_src.GetProjection() )
    
    in_src = None
    out_src = None
    
    return None
    
#%%
def usage():

    print("\n\t[-i Input File Directory]\n" \
    "\t[-name Input File Name (root only, e.g. ChangeMap)]\n" \
    "\n\tValid file names:\n" \
    "\tChangeMap, CoverMap, CoverDistMap, LastChange, QAMap, SegLength\n" \
    "\tChangeMagMap, YOLC, NumChanges\n" \
    "\n\t[-o Output Folder with complete path]\n\n")

    print("\n\tExample: 1_apply_colormap.py -i C:/.../CCDCMap -name " + \
          "ChangeMap -o C:/.../OutputFolder\n")

    print ""

    return None

#%%
def main():

    argv = sys.argv

    if argv is None:

        print "try -help"

        sys.exit(1)

    # Parse command line arguments.
    i = 1

    while i < len(argv):
        arg = argv[i]

        if arg == "-i":
            i = i + 1
            indir = argv[i]

        elif arg == "-name":
            i = i + 1
            name = argv[i]

        elif arg == "-o":
            i = i + 1
            outdir = argv[i]

        elif arg == "-help":
            usage()
            sys.exit(1)

        elif arg[:1] == ":":
            print("Unrecognized command option: %s" % arg)
            usage()
            sys.exit(1)

        i = i + 1

    indir = indir.replace("\\", "/")

    outdir = outdir.replace("\\", "/")

    outputdir = "%s/%s_color" % (outdir, name)

    filelist = sorted(glob.glob("{}/{}*.tif".format(indir, name)))

    if not os.path.exists(outputdir):

        os.makedirs(outputdir)

    print "\nFiles are saving in", outputdir, "\n"

    names = ["CoverMap", "CoverDistMap", "ChangeMap", "LastChange",\
             "SegLength", "QAMap", "ChangeMagMap"]

    colortables = ["color_covermap.txt", "color_covermap.txt",\
                   "color_changemap.txt", "color_lastchange.txt",\
                   "color_seglength.txt", "color_qa.txt",\
                   "color_changemag.txt"]

    dtypes = ["Byte", "Byte", "UInt16", "Byte", "Byte", "Byte", "Byte"]

    lookupcolor = dict(zip(names, colortables))

    lookuptype = dict(zip(names, dtypes))

    clrtable = lookupcolor[name]

    dtype = lookuptype[name]

    for r in filelist:

        r = r.replace("\\", "/")

        outfile = outputdir + "/" + os.path.basename(r)

        if not os.path.exists(outfile):

            print "Processing file ", r, "\n"
            # Call the primary function
            allCalc(r, outputdir, outfile, clrtable, dtype)

    return None

#%%
if __name__ == "__main__":

    main()

#%%
t2 = datetime.datetime.now()
print t2.strftime("%Y-%m-%d %H:%M:%S")
tt = t2 - t1
print "\nProcessing time: " + str(tt)
