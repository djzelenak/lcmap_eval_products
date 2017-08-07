'''
Create change layers from user defined time frame and interval (annuals).
Author: Devendra Dahal
Date:	8/5/2015
Last Updated: 2/3/2017 by Dan Zelenak to work on LCSRLNST01
'''

import os, sys, traceback, datetime, glob, subprocess, re, fnmatch
print sys.version

'''
try:
	from osgeo import gdal
	from osgeo.gdalconst import *
except ImportError:
	import gdal	
'''

t1 = datetime.datetime.now()
print t1.strftime("%Y-%m-%d %H:%M:%S")

GDALPath = '/usr/bin'

Layers2Years = {}
for i, j in zip(range(1,31),range(1985,2015)):
	# J = str(j)
	Layers2Years.update({j:i})

def allCalc(inDir, outDir, FromY, ToY, FileFormat) :
	try:
		#print 'in folder = %s' %(inDir) # for testing
		NLCDList = []
		NLCDList = glob.glob("%s/*.tif" %(inDir))
		NLCDList.sort()
		#pprint.pprint(NLCDList) # for testing
		
		NLCDYearList = []
		for NLCD in NLCDList:
			(dirName, fileName) = os.path.split(NLCD)
			NLCDYear = (re.split('[ _ .]',fileName)[1])[-4:]
			#print "Year is %s" % NLCDYear # for testing
			NLCDYearList.append(NLCDYear)
		NLCDYearList.sort()
		#pprint.pprint(NLCDYearList) # for testing
		
		if not os.path.exists(outDir):
			os.makedirs(outDir)
		if FromY == None and ToY == None:			
			for j in range(0,len(NLCDYearList)-1):
				if FileFormat == 'GTiff':
					FileF = 'GTiff'
					inputFile1 = NLCDList[j]
					inputFile2 = NLCDList[j+1]
					print "inputFile1 = %s\ninputFile2 = %s\n" %(inputFile1, inputFile2)
					Year1 = NLCDYearList[j]
					Year2 = NLCDYearList[j+1]
					year1,  year2 = str(Year1)[-2:], str(Year2)[-2:]
					print "Year 1 = %s\tYear 2 = %s\n" %(Year1,Year2)
					OutFile = "%s/nlcd%sto%scl.tif" %(outDir, year1, year2)
			
					if not os.path.exists(OutFile):
						runCalc  = '%s/gdal_calc.py --type %s -A %s -B %s --outfile %s --calc="(A * 100.0 + B)" ' \
						%(GDALPath,'UInt16',inputFile1,inputFile2,OutFile)
						subprocess.call(runCalc, shell=True) #--NoDataValue 0
					else:
						print "%s was already processed" %(os.path.basename(OutFile))
		else:
			if FileFormat == 'GTiff':
				FileF = 'GTiff'
				for f in NLCDList:
					if fnmatch.fnmatch(f, "%s/nlcd_%s*.tif" %(inDir, FromY)):
						inputFile1 = f
					elif fnmatch.fnmatch(f, "%s/nlcd_%s*.tif" %(inDir, ToY)):
						inputFile2 = f
				print "inputFile1 = %s\ninputFile2 = %s\n" %(inputFile1, inputFile2)
				year1,  year2 = str(FromY)[-2:], str(ToY)[-2:]
				print "Year 1 = %s\tYear 2 = %s\n" %(FromY,ToY)
				OutFile = "%s/nlcd%sto%scl.tif" %(outDir, year1, year2)
		
				if not os.path.exists(OutFile):
					runCalc  = '%s/gdal_calc.py --type %s -A %s -B %s --outfile %s --calc="(A * 100.0 + B)" ' \
					%(GDALPath,'UInt16',inputFile1,inputFile2,OutFile)
					subprocess.call(runCalc, shell=True) #--NoDataValue 0
				else:
					print "%s was already processed" %(os.path.basename(OutFile))
			
	except:
		print "Dang!! Something terrible happened"
		print traceback.format_exc()	

def usage():
	print ''
	print('Usage: python 4_nlcd_lc_change.py\n\n \
	[-i Input File path]\n \
	[-of outfile format (only 3 format supported: GTiff, HFA, and GRID)]\n \
	[-o Output Folder with complete path]\n\
	[-frm The "From" year]\n\
	[-to The "To" year]\n\n')
	print ''
	
def examps():
	print ''
	print('python 4_nlcd_lc_change.py -i /some/input/directory')
	print('-of GTiff -frm 1992 -to 2011 -o /some/output/directory\n')
	print ''

def main():
	fromY, toY, oFormat = None, None, None
	
	argv = sys.argv
		
	# Parse command line arguments.
	i = 1
	while i < len(argv):
		arg = argv[i]
		
		if arg == '-i':
			i           = i + 1
			inputDir     = argv[i]     

		elif arg == '-of':
			i           = i + 1
			oFormat      = argv[i]  
					
		elif arg == '-o':
			i           = i + 1
			outputDir         = argv[i] 

		elif arg == '-frm':
			i           = i + 1
			fromY       = argv[i]
		elif arg == '-to':
			i           = i + 1
			toY         = argv[i]
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

	if fromY == None:
		fromY = '1992'
	if toY == None:
		toY = '2011'
	if oFormat == None:
		oFormat = 'GTiff'
	
	if not os.path.exists(outputDir):
		os.makedirs(outputDir)

	# call the primary function
	allCalc(inputDir, outputDir, fromY, toY, oFormat)	

if __name__ == '__main__':
	main()	
t2 = datetime.datetime.now()
print t2.strftime("%Y-%m-%d %H:%M:%S")
tt = t2 - t1
print "\tProcessing time: " + str(tt) 
