'''
Description: Take CONUS NLCD layers and clip them to the extent of a given reference layer.
Based on script "RasterMask_reproject_resample_GDAL.py" by Devendra Dahal written on 5/12/2015
Last Updated: 1/10/2017, 2/2/2017 by Dan Zelenak
'''

import os, sys, traceback, datetime, glob, subprocess, pprint

print(sys.version)

# GDALpath = '/usr/bin'

try:
    from osgeo import gdal
# from osgeo.gdalconst import *
except ImportError:
    import gdal

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S"))


def GetExtent(gt, cols, rows):
    ''' Return list of corner coordinates from a geotransform

        @type gt:   C{tuple/list}
        @param gt: geotransform
        @type cols:   C{int}
        @param cols: number of columns in the dataset
        @type rows:   C{int}
        @param rows: number of rows in the dataset
        @rtype:    C{[float,...,float]}
        @return:   coordinates of each corner
    '''
    ext = []
    xarr = [0, cols]
    yarr = [0, rows]

    for px in xarr:
        for py in yarr:
            x = gt[0] + (px * gt[1]) + (py * gt[2])
            y = gt[3] + (px * gt[4]) + (py * gt[5])
            ext.append([x, y])
            # print x,y
        yarr.reverse()
    return ext


def GetGeoInfo(SourceDS):
    print('running GetGeoInfo function')
    # NDV 		= SourceDS.GetRasterBand(1).GetNoDataValue()
    cols = SourceDS.RasterXSize
    rows = SourceDS.RasterYSize
    bands = SourceDS.RasterCount
    GeoT = SourceDS.GetGeoTransform()
    proj = SourceDS.GetProjection()
    extent = GetExtent(GeoT, cols, rows)

    return cols, rows, GeoT, proj, bands, extent


"""
def NewRasterID(inFile,cols, rows,GeoTras, Projs, Value,OutFile):
	print '\n running NewRasterID function'
	band1 = inFile.GetRasterBand(1)
	Array1 = band1.ReadAsArray(0, 0, cols, rows)
	
	dsFile = rastDriver.Create(OutFile, cols, rows, 1, gdal.GDT_Byte)
	dsFile.SetGeoTransform(GeoTras)
	dsFile.SetProjection(Projs)
	NewArray = numpy.zeros(shape=(rows,cols)).astype(int)
	NewArray[numpy.where((Array1 >= 1))] = Value

	dsFile.GetRasterBand(1).WriteArray(NewArray) 
		
	dsFile = None
	inFile = None
"""


def ComputMask(inputD, ProjRaster, W, S, E, N, cSize, DestiProj):
    print('\n running ComputMask function')
    inMSSFile = gdal.Open(inputD)
    InXsize, InYsize, InGeoT, InProj, bands, extent = GetGeoInfo(inMSSFile)

    runwarp = "gdalwarp -of HFA -s_srs %s -overwrite -t_srs EPSG:5070 -te %s %s %s %s -tr %s %s -dstnodata 0 -q -r near %s %s" % \
              (InProj, W, S, E, N, cSize, cSize, inputD, ProjRaster)  ## -dstnodata 0
    subprocess.call(runwarp, shell=True)


def usage():
    print('Usage: python 2_clip_refdata.py\n\n'
          '[-i Input File Directory] \n'
          '[-ref Input reference file(used for clipping)]\n'
          '[-o Output Folder with complete path]\n\n')


def main():
    # RefFolder = None
    try:

        argv = sys.argv

        if argv is None:
            print("try -help")
            sys.exit(0)
        ## Parse command line arguments.
        i = 1
        while i < len(argv):
            arg = argv[i]

            if arg == '-i':
                i = i + 1
                inputDir = argv[i]

            elif arg == '-o':
                i = i + 1
                outputDir = argv[i]

            elif arg == '-ref':
                i = i + 1
                RefFile = argv[i]

            elif arg[:1] == ':':
                print('Unrecognized command option: %s' % arg)
                usage()
                sys.exit(1)

            elif arg == '-help':
                usage()
                sys.exit(1)

            i += 1

        inputList = sorted(glob.glob(inputDir + os.sep + '*.img'))
        print('Input Ref File List:\n')
        pprint.pprint(inputList)

        for inputD in inputList:

            # RefFile = '%s/ChangeMap_2000.tif' %(RefFolder) #arbitrary selection for reference file
            print('The reference file used for clipping is: {}\n'.format(os.path.basename(RefFile)))

            print('\tWorking on ', os.path.basename(inputD))
            if not os.path.exists(outputDir):
                os.makedirs(outputDir)

            tifDriver = gdal.GetDriverByName('GTiff')
            tifDriver.Register()
            tifMSSFile = gdal.Open(RefFile)
            Desxsize, Desysize, DesGeoT, DestiProj, desbands, dExt = GetGeoInfo(tifMSSFile)

            print('\n------------------------')
            print('Extent of the out layer:\n\t\t\t', dExt[3][1], '\n\n\t', dExt[0][0], '\t\t\t', dExt[2][0],
                  '\n\n\t\t\t', dExt[1][1])
            print('------------------------\n')
            W = str(dExt[0][0])
            S = str(dExt[1][1])
            E = str(dExt[2][0])
            N = str(dExt[3][1])

            cSize = DesGeoT[1]

            if not os.path.exists(outputDir):
                os.makedirs(outputDir)
            ProjRaster = outputDir + os.sep + os.path.basename(inputD).split('.')[0] + '.tif'
            ComputMask(inputD, ProjRaster, W, S, E, N, cSize, DestiProj)
            tifMSSFile = None

        print("\nAll done")
    except:
        print("Processed halted on the way.")
        print(traceback.format_exc())


if __name__ == '__main__':
    main()
t2 = datetime.datetime.now()
print(t2.strftime("%Y-%m-%d %H:%M:%S"))
tt = t2 - t1
print("\nProcessing time: " + str(tt))
