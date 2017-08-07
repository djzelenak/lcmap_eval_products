'''
Create change layers from user defined time frame and interval (annuals).
Author: Devendra Dahal
Date:	8/5/2015
Last Updated: 2/3/2017, 2/10/2017 by Dan Zelenak to work on LCSRLNST01
'''

import os, sys, traceback, datetime, time, glob, subprocess, pprint, re, fnmatch
import numpy as np

print sys.version

try:
	from osgeo import gdal
	from osgeo.gdalconst import *
except ImportError:
	import gdal	

t1 = datetime.datetime.now()
print t1.strftime("%Y-%m-%d %H:%M:%S")

GDALPath = '/usr/bin'

def allCalc(inDir, outDir, FileFormat, FromY, ToY, IntY) :
	try:
		#make output subdirectory if it doesn't exist
		if not os.path.exists(outDir):
			os.makedirs(outDir)

		#gather all .tif files in the input sub folder
		TrendsList = glob.glob(inDir + os.sep + "*.tif")
		#pprint.pprint(NLCDList) #for testing
		TrendsList.sort()
		TrendsYearList = []
		for Trends in TrendsList:
			(dirName, fileName) = os.path.split(Trends)
			TrendsYear = (re.split('[ _ .]',fileName)[1])[-4:]
			#print "Year is %s" % TrendsYear # for testing
			TrendsYearList.append(TrendsYear)
		TrendsYearList.sort()
		#pprint.pprint(TrendsYearList) # for testing
		# iterate through the trends block files for the current Tile to check if they contain useful data
		for t in range(len(TrendsList)-1, -1, -1): # go backwards through the list to avoid index errors
			test = gdal.Open(TrendsList[t])
			testband = test.GetRasterBand(1)
			testbanddata = testband.ReadAsArray()
			if np.all(testbanddata == 0):
				del TrendsList[t] # remove file from the list
				print "No Trends data for this tile and year %s\n" %(TrendsYearList[t] ) # for testing
				del TrendsYearList[t] #remove year from the list
				testbanddata, testband, test = None, None, None # clear these from memory
			testbanddata, testband, test = None, None, None
				# Skip processing this trends file because it's entirely nodata

		if FromY == None and ToY == None:
			for j in range(0, len(TrendsYearList)-1):
				if FileFormat == 'GTiff':
					FileF = 'GTiff'
					inputFile1 = TrendsList[j]
					inputFile2 = TrendsList[j+1]
					Year1 = TrendsYearList[j]
					if IntY != None:
						IntY = int(IntY)
						Year2 = int(TrendsYearList[j]) + IntY
						Year2 = str(Year2)
					else:
						Year2 = TrendsYearList[j+1]
					year1, year2 = str(Year1)[-2:], str(Year2)[-2:]
					OutFile = "%s/trends%sto%scl.tif" %(outDir, year1, year2)
				
					if not os.path.exists(OutFile):
						print "Working on change computation for year %s to year %s\n" \
						%(str(Year1), str(Year2))
						runCalc  = '%s/gdal_calc.py --type %s -A %s -B %s --outfile %s --calc="(A * 100.0 + B)" ' \
						% (GDALPath,'Int16',inputFile1,inputFile2,OutFile)
						subprocess.call(runCalc, shell=True) #--NoDataValue 0
					else:
						print "Already processed"	
		else:
	
			if not FromY in TrendsYearList:
				print "The -frm 'from' year  %s entered does not contain data for this tile" %(FromY)
				print "The following years are valid:"
				pprint.pprint (TrendsYearList)
				return
				
			if not ToY in TrendsYearList:
				print "The -to year %s entered does not contain data for this tile" %(ToY)
				print "The following years are valid:"
				pprint.pprint (TrendsYearList)
				return
				
			inputFile1 = "%s/Trendsblock_era%s.tif" %(inDir, FromY)
			inputFile2 = "%s/Trendsblock_era%s.tif" %(inDir, ToY)
			year1, year2 = FromY[-2:], ToY[-2:]
			OutFile = "%s/trends%sto%scl.tif" %(outDir, year1, year2)
			if not os.path.exists(OutFile):
				print "Working on change computation for year %s to year %s" %(FromY, ToY)
				runCalc = '%s/gdal_calc.py --type %s -A %s -B %s --outfile %s --calc="(A * 100.0 + B)" '\
				% (GDALPath,'Int16',inputFile1,inputFile2,OutFile)
				subprocess.call(runCalc, shell=True)
			else:
				print '%s was already processed' %(os.path.basename(OutFile))
				
	except:
		print "Dang!! Something terrible happened"
		print traceback.format_exc()	
		


	
def usage():
	print ''
	print('Usage:python  4_trendsera_lc_change.py\n\n \
	[-i Input File Directory]\n \
	[-of outfile format (only 3 format supported: GTiff, HFA, and GRID)]\n \
	[-frm From Year]\n \
	[-to To Year]\n \
	[-int Year Interval]\n \
	[-o Output Folder with complete path]\n\n')
	print ''
	
def examps():
	print ''
	print('Usage: python 4_trendsera_lc_change.py -i /some/directory\
	-of GTiff -frm 1989 -to 2010 -int 1 -o /some/directory\n')
	print ''

def main():
	oFormat, fromY, toY, intY = None, None, None, None
	
	argv = sys.argv
		
	if argv is None:
		print "try -help"
		sys.exit(1)

		
	# Parse command line arguments.
	i = 1
	while i < len(argv):
		arg = argv[i]
		
		if arg == '-i':
			i           = i + 1
			inputDir      = argv[i]     

		elif arg == '-of':
			i           = i + 1
			oFormat      = argv[i]  
		
		elif arg == '-frm':
			i           = i + 1
			fromY      = argv[i] 
		
		elif arg == '-to':
			i           = i + 1
			toY      = argv[i] 
		
		elif arg == '-int':
			i           = i + 1
			intY      = argv[i] 
			
		elif arg == '-o':
			i           = i + 1
			outputDir         = argv[i] 

		elif arg == '-help':
			usage()
			sys.exit(1) 
			
		elif arg == '-example':
			examps()
			sys.exit(1)                    
		
		elif arg[:1] == ':':
			print('Unrecognized command option: %s' % arg)
			usage()
			sys.exit(1)            

		i += 1
	
	if oFormat == None:
		oFormat = 'GTiff'
	
	if not os.path.exists(outputDir):
		os.makedirs(outputDir)
	
	# call the primary function
	allCalc(inputDir, outputDir, oFormat, fromY, toY, intY)	

if __name__ == '__main__':
	main()	
t2 = datetime.datetime.now()
print t2.strftime("%Y-%m-%d %H:%M:%S")
tt = t2 - t1
print "\tProcessing time: " + str(tt) 
