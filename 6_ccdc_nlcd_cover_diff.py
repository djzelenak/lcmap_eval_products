'''
Create change layers from user defined time frame and interval (annuals).
Author: Devendra Dahal
Date:	8/5/2015
Last Updated: 2/2/2017 by Dan Zelenak to work on LCSRLNST01, 
and 2/6/2017 to compute CCDC vs NLCD land cover from-to comparison (output 32-bit raster)
'''

import os, sys, traceback, datetime, time, glob, subprocess, fnmatch, pprint
print sys.version

try:
	from osgeo import gdal
	from osgeo.gdalconst import *
except ImportError:
	import gdal	

t1 = datetime.datetime.now()
print t1.strftime("%Y-%m-%d %H:%M:%S")

def allCalc(CCDCdir, NLCDdir, OutDir, FileFormat, FromY, ToY) : 
	try:
		fromY, toY = FromY[-2:], ToY[-2:] #extract last 2 digits from years to use for naming
		
		if not os.path.exists(OutDir):
			os.makedirs(OutDir)
		
		inCCDCList = glob.glob(CCDCdir + os.sep + "*.tif")
		inNLCDList = glob.glob(NLCDdir + os.sep + "*.tif")
		inCCDCList.sort()
		inNLCDList.sort()
		#pprint.pprint (inCCDCList) #for testing
		#pprint.pprint (inNLCDList) #for testing
		
		file1 = "%s/ccdc%sto%scl.tif" %(CCDCdir, str(fromY), str(toY))
		if not os.path.exists(file1):
			print "Need to compute change layers for CCDC year %s to year %s" %(FromY, ToY)
			sys.exit(1)
		
		file2 = "%s/nlcd%sto%scl.tif" %(NLCDdir, str(fromY), str(toY))		
		if not os.path.exists(file2):
			print "Need to compute change layers for NLCD year %s to year %s" %(FromY, ToY)
			sys.exit(1)
				
		bandFile = '%s/nlcd%sto%scl_ccdc%sto%scl.tif' %(OutDir, str(fromY), str(toY), str(fromY), str(toY))
		
		if not os.path.exists(bandFile):	
			#Only process if the output file doesn't already exist
			runCalc  = '/usr/bin/gdal_calc.py --format %s --type %s -A %s -B %s --outfile %s --calc="(A * 10000.0 + B)" '\
			%(FileFormat, 'Int32', file2, file1, bandFile) #first 3 or 4 digits are NLCD classes, last 4 digits are CCDC classes		
			subprocess.call(runCalc, shell=True) #--NoDataValue 0 
		else:
			print "Already processed"

	except:
		print "Dang!! Something terrible happened"
		print traceback.format_exc()

	
def usage():
	print ''
	print('Usage:python 6_ccdc_nlcd_cover_diff.py\n\n \
	[-ic Full path to the CCDC CoverDistMap layers]\n \
	[-ir Full path to the NLCD layers]\n\
	[-of outfile format (only 3 format supported: GTiff, HFA, and GRID)]\n \
	[-frm From Year]\n \
	[-to To Year]\n \
	[-o Output Folder with complete path]\n\n')
	print ''
	
def main():
	
	oFormat = None
	
	argv = sys.argv
		
	if argv is None:
		print "try -help"
		sys.exit(1)
		
	# Parse command line arguments.
	i = 1
	while i < len(argv):
		arg = argv[i]

		if arg == '-of':
			i           = i + 1
			oFormat      = argv[i]  
		elif arg == '-ic':
			i           = i + 1
			inputCCDC    = argv[i]  
		elif arg == '-ir':
			i           = i + 1
			inputNLCD   = argv[i]
		elif arg == '-o':              
			i           = i + 1
			outputDir   = argv[i]	
		elif arg == '-frm':
			i           = i + 1
			fromY      = argv[i] 
		elif arg == '-to':
			i           = i + 1
			toY      = argv[i] 
	
		i += 1

	if oFormat == None:
		oFormat = 'GTiff'
	
	# Call the primary function
	allCalc(inputCCDC, inputNLCD, outputDir, oFormat, fromY, toY)
	
if __name__ == '__main__':
	main()	
t2 = datetime.datetime.now()
print t2.strftime("%Y-%m-%d %H:%M:%S")
tt = t2 - t1
print "\tProcessing time: " + str(tt) 
