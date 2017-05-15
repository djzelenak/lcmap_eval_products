'''
Create change layers from user defined time frame and interval (annuals).
Author: Devendra Dahal
Date:	8/5/2015
Last Updated: 2/2/2017 by Dan Zelenak to work on LCSRLNST01 and
3/20/2017 to compute CCDC vs Trends change comparison (output int16)
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

Layers2Years = {}
for i, j in zip(range(1,31),range(1985,2015)):
	# J = str(j)
	Layers2Years.update({j:i})

def allCalc(inTrends, inCCDC, outDir, FileFormat, FromY, ToY) : 
	print "From Year: ", FromY
	try:
		
		if not os.path.exists(outDir):
			os.makedirs(outDir)

		inCCDCList = glob.glob(inCCDC + os.sep + "*.tif")
		inTrendsList = glob.glob(inTrends + os.sep + "*.tif")
		inCCDCList.sort()
		inTrendsList.sort()
		frmY, toY = FromY[-2:], ToY[-2:]
		file2 = '%s/ccdc%sto%sct.tif' %(inCCDC, FromY, ToY)
		file1 = '%s/trends%sto%sct.tif' %(inTrends, frmY, toY)
		print "\n\tmatched layers are: \n", file1,"\n", file2, "\n" #for testing
		if not os.path.exists(file1):
			print 'layer %s does not exist for this tile' %(os.path.basename(file1))
			return		
		print '\nFiles are saving in', outDir #for testing
			
		if FileFormat == 'GTiff':
			FileF = 'GTiff'
			bandFile = '%s/trends%sto%sct_ccdc%sto%sct.tif'	%(outDir, frmY, toY, frmY, toY)
			if not os.path.exists(bandFile):	
				runCalc  = '/usr/bin/gdal_calc.py --format %s --type %s -A %s -B %s --outfile %s --calc="(A * 100.0 + B)" ' \
				% (FileF, 'Int16',file1,file2,bandFile)			
				subprocess.call(runCalc, shell=True) #--NoDataValue 0 
			else:
				print "%s was already processed" %(os.path.basename(bandFile))
		else:
			print "use 'GTiff' for file format"
			sys.exit(1)

	except:
		print "Dang!! Something terrible happened"
		print traceback.format_exc()

	
def usage():
	print ''
	print 'Usage: Change_computation.exe\n\n \
	[-ic Full path to the input CCDC change map layers]\n \
	[-ir Full path to the input Trends change map layers]\n\
	[-of outfile format (only 3 format supported: GTiff, HFA, and GRID)]\n \
	[-frm From Year]\n \
	[-to To Year]\n \
	[-o Main output directory]\n\n'
	print ''
	
def main():
	oFormat, fromY, toY = None, None, None
	argv = sys.argv
		
	if argv is None:
		print "try -help"
		sys.exit(1)

	# Parse command line arguments.
	i = 1
	while i < len(argv):
		arg = argv[i]
		
		if arg == '-ir':
			i           = i + 1
			inputTrends      = argv[i]     
		
		elif arg == '-ic':
			i           = i + 1
			inputCCDC = argv[i]

		elif arg == '-of':
			i           = i + 1
			oFormat      = argv[i]  
		
		elif arg == '-frm':
			i           = i + 1
			fromY      = argv[i] 
		
		elif arg == '-to':
			i           = i + 1
			toY      = argv[i] 
		
		elif arg == '-o':
			i           = i + 1
			outputDir         = argv[i] 

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
	if fromY == None:
		fromY = '1992'
	if toY == None:
		toY = '2011'
			
	allCalc(inputTrends, inputCCDC, outputDir, oFormat, fromY, toY)
	
if __name__ == '__main__':
	main()

t2 = datetime.datetime.now()
print t2.strftime("%Y-%m-%d %H:%M:%S")
tt = t2 - t1
print "\tProcessing time: " + str(tt) 
