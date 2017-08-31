#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Dan Zelenak
Based on script originally written by Dev Dahal
Last Updated 5/16/2017
"""

import os, sys, datetime, glob, subprocess, pprint, re

print (sys.version)

try:
    from osgeo import gdal
    # from osgeo.gdalconst import *
except ImportError:
    import gdal    


t1 = datetime.datetime.now()
print (t1.strftime("%Y-%m-%d %H:%M:%S"))

gdal.UseExceptions()
gdal.AllRegister()

#%%
def GetExtent(gt,cols,rows):
    
    """ Return list of corner coordinates from a geotransform

        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner
    
    """
    
    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        
        for py in yarr:
            
            x=gt[0]+(px*gt[1])+(py*gt[2])
            
            y=gt[3]+(px*gt[4])+(py*gt[5])
            
            ext.append([x,y])
            
            # print x,y
        
        yarr.reverse()
    
    return ext

#%%
def GetGeoInfo(SourceDS):
    
    """Obtain information about the transformation, projection, and size
    of the raster dataset
    
    Args:
        SourceDS = gdal raster object
        
    Returns:
        cols = 
        rows = 
        bands = 
        GeoT = 
        proj = 
        extent = 
    """
    
    
    print ('running GetGeoInfo function')
    # NDV         = SourceDS.GetRasterBand(1).GetNoDataValue()
    cols         = SourceDS.RasterXSize
    rows         = SourceDS.RasterYSize
    bands         = SourceDS.RasterCount
    GeoT         = SourceDS.GetGeoTransform()
    proj         = SourceDS.GetProjection()
    extent        = GetExtent(GeoT, cols, rows)
    
    return cols, rows, GeoT, proj, bands, extent

#%%
def ComputMask(inputD, ProjRaster,W,S,E,N, cSize, DestiProj):
    
    """
    """
    
    print ('\n running ComputMask function')
    inMSSFile = gdal.Open(inputD)
    InXsize, InYsize, InGeoT, InProj, bands, extent = GetGeoInfo(inMSSFile)
    
    runwarp = "gdalwarp -of HFA -s_srs %s -overwrite -t_srs %s -te %s %s %s %s -tr %s %s -dstnodata 0 -q -r near %s %s" % \
    (InProj,DestiProj, W, S, E, N, cSize,cSize, inputD, ProjRaster) ## -dstnodata 0
    
    subprocess.call(runwarp, shell=True)
    
    return None

#%%
def RemoveEmpty(raster):
    
    """Open the clipped Trends rasters and delete those that are entirely
    no data.
    
    Args:
        raster (str) = path to the Trends raster being tested
    
    Returns:
        None
    """
    import numpy as np
    
    test = gdal.Open(raster)
    
    testband = test.GetRasterBand(1)
    
    testbanddata = testband.ReadAsArray()
    
    if np.all(testbanddata == 0):
    
        test, testband, testbanddata = None, None, None
        
        os.remove(raster)
        
        ancillary = glob.glob(raster + '*') # remove associated files too (.aux)
        
        for i in ancillary:
            
            os.remove(i)
            
        print ('%s is entirely no data and it has been removed' %(os.path.basename(raster)))
    
    allfiles = glob.glob(raster + "*")
        
    for anc in allfiles:
            
        anc_ = re.sub("era", "", anc)
        
        os.rename(anc, anc_)

    return None

#%%
def usage():

    print('\n\n \
    [-i Input File Directory] \n \
    [-ref Input reference file Directory (used for clipping NLCD)]\n \
    [-o Output Folder with complete path]\n\n')
    
    return None

#%%
def main():

    argv = sys.argv
        
    if argv is None:
        print ("try -help")
        sys.exit(0)
    ## Parse command line arguments.
    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg == '-i':
            i           = i + 1
            inputDir    = argv[i]        
        
        elif arg == '-o':
            i           = i + 1
            outputDir   = argv[i] 
        
        elif arg == '-ref':
            i           = i + 1
            RefFile     = argv[i]     
        
        elif arg[:1] == ':':
            print('Unrecognized command option: %s' % arg)
            usage()
            sys.exit(1)
        
        elif arg == '-help':
            usage()
            sys.exit(1) 
        
        i += 1

    inputList = sorted(glob.glob(inputDir + os.sep + '*.img'))        
    
    print ('Input File List:\n')
    pprint.pprint(inputList)
    
    for inputD in inputList:
        # RefFile = '%s/ChangeMap_2000.tif' %(RefFolder) #arbitrary selection for reference file
        print ('\n\tWorking on', inputD.split('/')[-1])
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)

        # tifDriver = gdal.GetDriverByName('GTiff')
        # tifDriver.Register()
        ref = gdal.Open(RefFile)
        Desxsize, Desysize, DesGeoT, DestiProj, desbands, dExt = GetGeoInfo(ref)
        
        print ('\n------------------------')
        print ('Extent of the out layer:\n\t\t\t',dExt[3][1],'\n\n\t',dExt[0][0],
        '\t\t\t',dExt[2][0],'\n\n\t\t\t',dExt[1][1])
        print ('------------------------\n')
        
        W = str(dExt[0][0])
        S = str(dExt[1][1])
        E = str(dExt[2][0])
        N = str(dExt[3][1])

        cSize = DesGeoT[1]


        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        
        ProjRaster = outputDir + os.sep + os.path.basename(inputD).split('.')[0]+ '.tif'
        
        if not os.path.exists(ProjRaster):
            ComputMask(inputD,ProjRaster,W,S,E,N,cSize,DestiProj)
            RemoveEmpty(ProjRaster)    #check if empty dataset
        
        else:
            print ('%s already exists' %(os.path.basename(ProjRaster)))
            RemoveEmpty(ProjRaster)    #check if empty dataset

    print ("\nAll done")
    
    return None

#%%
if __name__ == '__main__':
    main()
t2 = datetime.datetime.now()
print (t2.strftime("%Y-%m-%d %H:%M:%S"))
tt = t2 - t1
print ("\nProcessing time: " + str(tt) )
