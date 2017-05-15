'''
Original Script Name: Frequency_computation.py
Author: Devendra Dahal
Date:	8/18/2015
Last Updated : 2/6/2017 by Dan Zelenak to work on LCSRLNST01
'''

import os, sys, traceback, datetime, time,numpy,glob, subprocess, re, pprint, fnmatch
print sys.version

try:
	from osgeo import gdal
	from osgeo.gdalconst import *
except ImportError:
	import gdal	

GDALPath = '/usr/bin'

t1 = datetime.datetime.now()
print "Processing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n")

def errMsg(i, Year):
	print "\n----------\nOooops!! assigned",i,"year (",str(Year),") is not valid. Please check your input folder for valid", i, "year.\n--------\n"
	os._exit(1)

## function to read properties of a raster file
def GetGeoInfo(SourceDS):
	RasB 		= SourceDS.GetRasterBand(1)
	# NDV 		= SourceDS.GetRasterBand(1).GetNoDataValue()
	xsize 		= SourceDS.RasterXSize
	ysize 		= SourceDS.RasterYSize
	bands	 	= SourceDS.RasterCount
	GeoT 		= SourceDS.GetGeoTransform()
	proj 		= SourceDS.GetProjection()
	ColorT		= RasB.GetRasterColorTable()
	DataType 	= RasB.DataType
	DataType 	= gdal.GetDataTypeName(DataType)
	
	return xsize, ysize, GeoT, proj, DataType, bands

def RasterChange1(inDir,frmY, toY, FFormat, OutFile, ext):
	RasterList = glob.glob(inDir + os.sep + "*" +ext)	
	RasterList = sorted(RasterList)
	print len(RasterList)
	sys.exit()
	##--------GDAL reading file and file information--------
	inFile = gdal.Open(RasterList[0])
	cols, rows, geot, proj, DataType, bands = GetGeoInfo(inFile)		
	newArray = numpy.zeros(shape=(rows,cols)).astype(int)
	##-------end reding information---------
		
	# re.split('[, \r\n]',row)
	minYear = os.path.basename(RasterList[0]).split(".")[0].split("_")[1].split("-")[0]	
	intYear = os.path.basename(RasterList[1]).split(".")[0].split("_")[1].split("-")[0]
	maxYear = os.path.basename(RasterList[-1]).split(".")[0].split("_")[1].split("-")[0]
	
	inY = int(intYear) - int(minYear)
	if inY == 0:
		print "\n-------------------\nOooops!! The input folder seems to have files for multiple interval of change. \
		This may create wrong frequency output. Please check and make sure\
		consistency of interval among change layers.\n----------------------\n"
		os._exit(1)
	if int(frmY) < int(minYear):
		errMsg("FROM",frmY)
	if int(toY) > int(maxYear):
		errMsg("TO",toY)
	div = int(frmY) % int(minYear)
	div2 = div % inY
	if div != 0 and div2 != 0:
		print "\n-------------------\nOooops!! Asking 'From' year is not matching in the input files. \
		Please make sure change layers was computed for the 'From' year, you are asking.\n----------------------\n"
		os._exit(1)
	print '0 ..',
	for i, Year in enumerate(range(int(frmY), int(toY)-inY, inY)):
		Year2 = int(Year+inY)
		file1 = glob.glob(inDir +os.sep + "Change*_"+str(Year)+"*"+ext)[0]
		file2 = glob.glob(inDir +os.sep + "Change*_"+str(Year2)+"*"+ext)[0]
		# file2 = glob.glob(inDir +os.sep + "*-"+str(Year)+"."+ext)[0]
	
		ff = int(frmY)
		dif = int(toY) - ff		
		ii = int(((i+i+int(inY))/float(dif)) *100)
		print ii,'..',
		# sys.exit()
		(dirName, fileName) = os.path.split(file1)
		
		inFile1 = gdal.Open(file1)	
		inFile2 = gdal.Open(file2)	
		
		band1 = inFile1.GetRasterBand(1)
		band2 = inFile2.GetRasterBand(1)
		Array1 = band1.ReadAsArray(0, 0, cols, rows)
		Array2 = band2.ReadAsArray(0, 0, cols, rows)

		ArrayT = (Array1 != Array2).astype(int)

		newArray += ArrayT
	
	driver = gdal.GetDriverByName(FFormat)
	dst_ds = driver.Create(OutFile, cols, rows, bands, GDT_Int16)
	dst_ds.SetGeoTransform(geot)
	dst_ds.SetProjection(proj)	
	dst_ds.GetRasterBand(1).WriteArray(newArray)
	print '100 - Done'
	# ListArray.append(OutFile)
	newArray = None
	return OutFile

def RasterChange(FFormat,outputDir,RasterList,exten, OutFile):
	print 'raster list length = ',len(RasterList) #for testing
	print RasterList
	runCalc0  = '%s/gdal_calc.py --format %s --type %s -A %s --outfile %s --calc="0 *(A > 0)" ' \
	% (GDALPath, FFormat,'Int16', RasterList[0], OutFile)			
	subprocess.call(runCalc0, shell=True)
	for i in range(len(RasterList)-1):
		
		f1 = RasterList[i]
		f2 = RasterList[i+1]
		#f1 = RasterList[0]
		#f2 = RasterList[1]
		
		file3 = outputDir + os.sep + 'zzzz' + exten
		runCalc1  = '%s/gdal_calc.py --format %s --type %s -A %s -B %s --outfile %s --calc="1 *(A != B)" ' \
		% (GDALPath, FFormat,'Int16',f1,f2,file3)			
		subprocess.call(runCalc1, shell=True)
		
		OutFiles = outputDir + os.sep + 'zzzz_' +str(i)+exten
		if not os.path.exists(OutFiles):
			runCalc2  = '%s/gdal_calc.py --format %s --type %s -A %s -B %s --outfile %s --calc="(A + B)" --overwrite ' \
			% (GDALPath, FFormat,'Int16',file3,OutFile,OutFiles)	
			OutFile = OutFiles
			subprocess.call(runCalc2, shell=True)
			
	return OutFiles
	
def RasterChangeGrid1(outputDir,RasterList,FfFormat, OutFile):
	print "Using numpy"
	
	f1 = RasterList[0].split('.')[0]
	file1 = outputDir + os.sep + 'zzzzx.tif'	
	runsubset2a  = GDALPath + os.sep + 'gdal_translate -of %s -q %s %s -a_nodata 0' % (FfFormat,f1,file1)		
	subprocess.call(runsubset2a, shell=True)

	inFile = gdal.Open(f1)
	cols, rows, geot, proj, DataType, bands = GetGeoInfo(inFile)		
	
	newArray = numpy.zeros(shape=(rows,cols)).astype(int)
	for i in range(len(RasterList)-1):
		f1a = RasterList[i].split('.')[0]
		f1b = RasterList[i+1].split('.')[0]

		file1a = outputDir + os.sep + 'zzzza1.tif'
		file1b = outputDir + os.sep + 'zzzza2.tif'		
		
		runsubset2a  = '%s\gdal_translate -of %s -q %s %s -a_nodata 0' % (GDALPath, FfFormat,f1a,file1a)		
		subprocess.call(runsubset2a, shell=True)

		runsubset2b  = '%s\gdal_translate -of %s -q %s %s -a_nodata 0' % (GDALPath, FfFormat,f1b,file1b)				
		subprocess.call(runsubset2b, shell=True)
		
		inFile1 = gdal.Open(file1a)	
		inFile2 = gdal.Open(file1b)	
		
		band1 = inFile1.GetRasterBand(1)
		band2 = inFile2.GetRasterBand(1)
		Array1 = band1.ReadAsArray(0, 0, cols, rows)
		Array2 = band2.ReadAsArray(0, 0, cols, rows)

		ArrayT = (Array1 != Array2).astype(int)

		newArray += ArrayT
	
	driver = gdal.GetDriverByName(FFormat)
	dst_ds = driver.Create(OutFile, cols, rows, bands, GDT_Byte)
	dst_ds.SetGeoTransform(geot)
	dst_ds.SetProjection(proj)	
	dst_ds.GetRasterBand(1).WriteArray(newArray)

	# ListArray.append(OutFile)
	newArray = None
	return OutFile
	
def RasterChangeGrid(outputDir,inputD,fromY, toY, FfFormat, OutFile):
	RasterList = sorted(glob.glob(inputD + os.sep + "*.tif"))
	
	minYear = int(os.path.basename(RasterList[0]).split("-")[0][1:])
	intYear = os.path.basename(RasterList[1]).split("-")[0][1:]
	maxYear = os.path.basename(RasterList[-1]).split(".")[0].split("-")[1]
	
	inY = int(intYear) - int(minYear)
	if inY == 0:
		print "\n-------------------\nOooops!! The input folder seems to have files for multiple interval of change. \
		This may create wrong frequency output. Please check and make sure\
		consistency of interval among change layers.\n----------------------\n"
		os._exit(1)
	if int(fromY) < int(minYear):
		errMsg("FROM",frmY)

	if int(toY) > int(maxYear):
		errMsg("TO",toY)
	div = int(fromY) % int(minYear)
	div2 = div % inY

	if div != 0 and div2 != 0:
		print "\n-------------------\nOooops!! Asking 'From' year is not matching in the input files. \
		Please make sure change layers was computed for the 'From' year, you are asking.\n----------------------\n"
		os._exit(1)
	runCalc0  = '%s\gdal_calc --type %s -A %s --outfile %s --calc="0 *(A > 0)" ' % (GDALPath, 'Int16', RasterList[0],OutFile)			
	subprocess.call(runCalc0, shell=True)
	runCalc0 = None	
	for i, Year in enumerate(range(int(fromY), int(toY)-inY, inY)):
		Year2 = int(Year+inY)
		f1 = glob.glob(inputD +os.sep + "Y"+str(Year)+"-*.asc")[0]
		f2 = glob.glob(inputD +os.sep + "Y"+str(Year2)+"-*.asc")[0]
		
		# f1 = RasterList[i]#.split('.')[0]
		# f2 = RasterList[i+1]#.split('.')[0]

		file3 = outputDir + os.sep + 'zzzz3.tif'
		runCalc1  = '%s\gdal_calc --type %s -A %s -B %s --outfile %s --calc="1 *(A != B)" ' % (GDALPath, 'Int16',f1,f2,file3)			
		subprocess.call(runCalc1, shell=True)
		
		OutFiles = outputDir + os.sep + 'zzzzz' +str(i)+'.tif'
		if not os.path.exists(OutFiles):
			runCalc2  = '%s\gdal_calc --type %s -A %s -B %s --outfile %s --calc="(A + B)" --overwrite ' % (GDALPath, 'Int16',file3,OutFile,OutFiles)	
			OutFile = OutFiles
		subprocess.call(runCalc2, shell=True)
		
	return OutFile
	
def allCalc(inputDir, outputDir, FileFormat, FromY, ToY):

	if not os.path.exists(outputDir):
		os.makedirs(outputDir)
	
	TrendsList = glob.glob(inputDir + os.sep + "*.tif")
	TrendsList.sort()
		
	FileList = []
	for x in TrendsList:
		dir, filex = os.path.split(x)
		FileList.append(filex)
		
	YearList = []
	for y in FileList:
		Year = (re.split('[ _ .]',y)[1])[-4:]
		YearList.append(Year)
	print 'Trends block years for this tile:\n'
	pprint.pprint(YearList) # for testing
	
	if FromY == None:
		FromY = YearList[0]
		print FromY # for testing
	if ToY == None:
		ToY = YearList[-1]
		print ToY # for testing
	for i in range(0,len(YearList)):
		try:
			if int(YearList[0]) < int(FromY):
				del TrendsList[0]
				del YearList[0]
			elif int(YearList[-1]) > int(ToY):
				del TrendsList[-1]
				del YearList[-1]
		except:
			IndexError
	pprint.pprint(TrendsList) #for testing
	
	frmY, toY = FromY[-2:], ToY[-2:]  # used for output file naming
	
	try:
	
		if FileFormat == 'GTiff':
			FFormat = 'GTiff'
			exten = '.tif'
			rastDriver = gdal.GetDriverByName(FFormat) # reading gdal driver 
			rastDriver.Register()
			OutFile = '%s/trends%sto%sct.tif' %(outputDir, frmY, toY)
			#print "\tOutFile: ", OutFile #for testing
			# cumulativeChange = RasterChange1(inputDir,frmY, toY,FFormat, OutFile, exten)
			if not os.path.exists(OutFile):
				print 'working on change frequency for years %s to %s' %(FromY, ToY)
				cumulativeChange = RasterChange(FFormat, outputDir, TrendsList, exten, OutFile)
				runsubset3  = '%s/gdal_translate -of %s -q %s %s ' % (GDALPath, FFormat, cumulativeChange, OutFile)				
				subprocess.call(runsubset3, shell=True)
			else:
				print '%s already exists' %(os.path.basename(OutFile))
	
		elif FileFormat == 'HFA':
			FFormat = 'HFA'
			exten = '.img'
			rastDriver = gdal.GetDriverByName(FFormat) # reading gdal driver 
			rastDriver.Register()
			
			OutFile = '%s/trends%sto%sct%s' %(outputDir, frmY, toY, exten)
			print "\tOutFile: ", OutFile
			
			cumulativeChange = RasterChange(FFormat,outputDir, TrendsList,exten, OutFile)
		
		elif FileFormat == 'GRID':
			FFormat = 'AAIGrid'
			OutFile = outputDir + os.sep + "zzzz.tif"
			OutFile1 = '%s/trends%sto%sct.asc' %(outputDir, frmY, toY)
			print "\tOutFile: ", OutFile1
			cumulativeChange = RasterChangeGrid(outputDir, inputDir, frmY, toY, 'GTiff', OutFile)
			
			runsubset2  = GDALPath + os.sep+'gdal_translate -of %s -q %s %s ' % (FFormat, cumulativeChange, OutFile1)				
			subprocess.call(runsubset2, shell=True)
		
		for v in glob.glob(outputDir + os.sep+ "zzz*"):
			os.remove(v)
			
	except:
		print "Opps! something is not working"
		print traceback.format_exc()
		print  "Unexpected error:", sys.exc_info()[0]
	
def usage():
	print ''
	print('Usage: python 5_trends_change_freq.py\n\n \
	[-i Input Folderpath where change layers are saved] \n\
	[-frm From Year]\n \
	[-to To Year]\n \
	[-o Output Folderpath] \n \
	[-if input File Format (only 3 format supported: GTiff, HFA, and GRID)] \n\n \
	Output raster will be saved in the same format as input raster.\n\n')
	print ''
	
def examps():
	print ''
	print('Usage:python 5_trends_change_freq.py -i /some/directory -frm 1989 -to 2002 -o /some/directory -if GTiff \n')
	print ''

def main():
	oFormat, fromY, toY = None, None, None
	
	argv = sys.argv
		
	if argv is None:
		sys.exit(0)

	# Parse command line arguments.
	i = 1
	while i < len(argv):
		arg = argv[i]

		if arg == '-i':
			i           = i + 1
			inputDir        = argv[i]        
		
		elif arg == '-frm':
			i           = i + 1
			fromY      = argv[i] 
		
		elif arg == '-to':
			i           = i + 1
			toY      = argv[i] 	
		
		elif arg == '-o':
			i           = i + 1
			outputDir      = argv[i]     

		elif arg == '-if':
			i           = i + 1
			oFormat      = argv[i]       

		elif arg == '-help':
			usage()
			sys.exit(1) 
			
		elif arg[:1] == ':':
			print('Unrecognized command option: %s' % arg)
			usage()
			sys.exit(1)            

		i += 1
	
	if oFormat == None:
		oFormat = 'GTiff'
	
	# call the primary function
	allCalc(inputDir, outputDir, oFormat, fromY, toY)

if __name__ == '__main__':
	main()     

t2 = datetime.datetime.now()
print "\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S")

tt = t2 - t1
print "Processing time: " + str(tt),"\n"
