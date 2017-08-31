'''
Original Script Name: Frequency_computation.py
Author: Devendra Dahal
Date:	8/18/2015
Last Updated : 3/7/2017 by Dan Zelenak, 3/9/2017 by Dan Zelenak to work LCSRLNST01
Description:  Go through ChangeMap layers in reverse (ie start at 2016 and work back to 1985)
and flag each pixel when the first change is detected going back through time.  The result is a single raster
that shows in which year the last registered change occured.
'''

import os, sys, traceback, datetime, glob, subprocess, re, pprint

print (sys.version)

GDALPath = '/usr/bin'
#GDALPath = r'C:\Users\dzelenak\Workspace\Testing\LCMAP_Tools\dist'

try:
	from osgeo import gdal
	from osgeo.gdalconst import *
except ImportError:
	import gdal

t1 = datetime.datetime.now()
print ("Processing started at: ", t1.strftime("%Y-%m-%d %H:%M:%S\n"))

def add_color_table(in_vrt, clr_table, dtype):
	color_table = open(clr_table, 'r')

	(dirName, fileName) = os.path.split(in_vrt)
	(fileBase, fileExt) = os.path.splitext(fileName)

	out_vrt = r'{0}{1}zzzzz{2}_temp.vrt'.format(dirName, os.sep, fileBase)

	in_txt = open(in_vrt, 'r+')
	out_txt = open(out_vrt, 'w')

	with open(in_vrt, 'r+') as in_txt, open(out_vrt, 'w') as out_txt:
		# key is the line after which to insert the color table in the new VRT text
		key = '<VRTRasterBand dataType="{0}" band="1">'.format(dtype)
		# subkey is a line that doesn't need to be in the new VRT text
		subkey = '   <ColorInterp>Gray</ColorInterp>'
		# get lines in a list
		txt_read = in_txt.readlines()

		for line in txt_read:
			if subkey in line:
				#print '\nfound the subkey to ignore\n'
				continue
			else:
				writetxt = r'{0}'.format(line)
				out_txt.write(writetxt)

				# insert color table following keywords
				if key in line:
					#print "\nFound the key!\n"
					color_read = color_table.readlines()
					#print 'writing color table to vrt'
					for ln in color_read:
						out_txt.write(ln)
		#print 'done writing!'
	return out_vrt
	# (FFormat, outDir, rList, exten, tempoutfile)

def RasterChange(fformat, outdir, rasterlist, exten, outfile):
	#create outfile raster of all 0's that matches the format of the first raster in rasterlist
	#**stored in the outfile raster**

	runCalc0  = '%s/gdal_calc.py --format %s --type %s -A %s --outfile %s --calc="0 *(A > 0)" ' \
	% (GDALPath, fformat, 'Int16', rasterlist[0], outfile)
	#print 'running calculate zeros\n'
	subprocess.call(runCalc0, shell=True)

	for i in range(len(rasterlist)): #Changed rasterlist - 1 to rasterlist, to count last raster if change occured
		raster1 = rasterlist[i]

		raster1out = outdir + os.sep + 'xxxx_raster1out' + exten

		# raster1out stores the yes/no change layer for rasterlist[i]
		runCalc1  = '%s/gdal_calc.py --format %s --type %s -A %s --outfile %s --calc="1 *(A > 0)" ' \
		% (GDALPath, fformat, 'Int16', raster1, raster1out)

		subprocess.call(runCalc1, shell=True)

		tempraster = outdir + os.sep + 'xxxx_' + str(i) + exten

		if not os.path.exists(tempraster):
			# tempraster holds the sum of the yes/no raster1out and the outfile
			runCalc2  = '%s/gdal_calc.py --format %s --type %s -A %s -B %s --outfile %s --calc="(A + B)" --overwrite'\
			 % (GDALPath, fformat, 'Int16', raster1out, outfile, tempraster)

			# outfile gets updated with the new sum
			outfile = tempraster
			#print '\nrunning change calculation\n'
			subprocess.call(runCalc2, shell=True)

	return tempraster


def readData(raster):
	#Load raster data into array
	print ('loading raster {}\n'.format(raster))
	filedata = gdal.Open(raster, gdal.GA_ReadOnly).ReadAsArray()
	return filedata


def allCalc(inDir, outDir, FileFormat, FromY, ToY):
	try:
		# create main output directory if it doesn't exist
		if not os.path.exists(outDir):
			os.makedirs(outDir)

		FFormat = 'GTiff'
		exten = '.tif'
		rastDriver = gdal.GetDriverByName(FFormat) # reading gdal driver
		rastDriver.Register()
		
		RasterList = glob.glob('%s/ChangeMap*%s' %(inDir, exten))
		RasterList.sort()
		#del(RasterList[-1:])
		YearList = []
		pprint.pprint(RasterList)
		
		for x in RasterList:
			dir, filex = os.path.split(x)
			Year = (re.split('[ _ .]',filex)[1])[-4:]
			YearList.append(Year)
		YearList.sort()
		pprint.pprint(YearList)
		#clip year list using from/to years if passed
		#if not FromY == None and ToY == None:
		for i in range(0,len(YearList)):
			try:
				if int(YearList[0]) < int(FromY):
					del RasterList[0]
					del YearList[0]
				elif int(YearList[-1]) > int(ToY):
					del RasterList[-1]
					del YearList[-1]
			except:
				IndexError
		else:
			FromY, ToY = YearList[0], YearList[-1]
		
		###----------calculation_for_year_of_last_change--------------
		pprint.pprint(RasterList)
		pprint.pprint(YearList)
		
		#final output raster**
		out_file = '{}{}ccdc{}to{}yolc.tif'.format(outDir, os.sep, FromY[-2:], ToY[-2:])
		
		#temp output of change calculations
		temp_out = '{}{}zzzz{}to{}yolc.tif'.format(outDir, os.sep, FromY[-2:], ToY[-2:])
		
		#temp out for color table
		temp_out2 = '{}{}zzzz2{}to{}yolc.tif'.format(outDir, os.sep, FromY[-2:], ToY[-2:])
		
		#Generate the output raster with all zero values for now
		runCalc0  = '%s/gdal_calc.py --format %s --type %s -A %s --outfile %s --calc="0 *(A > 0)" ' \
		% (GDALPath, 'GTiff', 'Byte', RasterList[0], temp_out)
		subprocess.call(runCalc0, shell=True)
		#-----#
		p = 1
	
		for i in range(len(RasterList)-1, -1, -1):
			print ('checking image {0}'.format(RasterList[i]))
			
			raster1 = RasterList[i]
			raster1out = outDir + os.sep + 'zzzz_raster1out' + exten
			
			# print (YearList[i])
			
			proc = '{}{}gdal_calc.py -A {} --outfile {} --format GTiff --type UInt16 --calc="{}*(A > 0)"'.format(GDALPath, os.sep, raster1, raster1out, YearList[i])
			subprocess.call(proc, shell=True)
			
			#temp output of the next process
			tempraster = '{}{}zzzzz{}.tif'.format(outDir, os.sep, str(i))
			
			'''
			raster1out now is a raster with values 0 or Year.  Compare this with temp_out, which initially is all 0's.
			For the first time through the loop, any pixel with a Year value is preserved, or is supposed to be.
			temp_out is then made to equal the output of this test which is tempraster.  This continues for each iteration, 
			but rather than all 0's, temp_out will now contain Year values for some pixels.  
			'''
			
			if not os.path.exists(tempraster):
				proc2 = '{}{}gdal_calc.py -A {} -B {} --outfile {} --format GTiff --type UInt16  --calc="(A * (B == 0)) + B"'.format(GDALPath, os.sep, raster1out, temp_out, tempraster)
				
				# outfile gets updated with the new sum
				temp_out = tempraster
				
				subprocess.call(proc2, shell=True)
				
			p += 1
			
		runsubset3 = '%s/gdal_translate -of %s -ot UInt16 -q %s %s ' % (GDALPath, FFormat, tempraster, temp_out2)
		subprocess.call(runsubset3, shell=True)
	
		###--------color_pallette---------------------
		clr_table = 'color_yolc.txt'

		outcsv_File = r'%s/zzzzzz_%s_to_%s_list.csv' % (outDir, FromY[-2:], ToY[-2:])
		if os.path.isfile(outcsv_File):
			os.remove(outcsv_File)

		with open(outcsv_File, 'wb') as outcsv2_File:
			outcsv2_File.write(temp_out2.encode('utf-8') + "\r\n".encode('utf-8'))

		out_VRT = '{0}{1}zzzz_{2}-{3}.vrt'.format(outDir, os.sep, FromY[-2:], ToY[-2:])
		com	= '%s/gdalbuildvrt -q -input_file_list %s %s' % (GDALPath, outcsv_File, out_VRT)
		subprocess.call(com, shell=True)

		out_vrt = add_color_table(out_VRT, clr_table, 'UInt16')
		runCom  = '%s/gdal_translate -of %s -ot UInt16  -stats -a_srs EPSG:5070 -q -a_nodata 0  %s %s' % (GDALPath, FFormat, out_vrt, out_file)
		subprocess.call(runCom, shell=True)

		# remove the temp files used for adding the color tables
		for v in glob.glob(outDir + os.sep+ "zzz*"):
			os.remove(v)
			
	except:
		print ("Opps! something is not working")
		print (traceback.format_exc())
		print  ("Unexpected error:", sys.exc_info()[0])

def usage():

	print('\nUsage:python 5_ccdc_change_accumulation.py\n\n \
	[-i Full path to the directory containing the CCDC annual change layers] \n\
	[-frm From Year]\n \
	[-to To Year]\n \
	[-o Output Folderpath] \n \
	[-if input File Format (only 3 format supported: GTiff, HFA, and GRID)] \n \
	The output raster will be saved in the same format as the input raster.\n\
	Output raster will be saved in the same format as input raster.\n\n')


def examps():

	print('\nUsage:python 5_ccdc_change_accumulation.py -i /some/InputDir -frm 1989 -to 2002 -o /some/OutDir -if GTiff \n')


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
	
	# call the primary function	
	allCalc(inputDir, outputDir, oFormat, fromY, toY)

if __name__ == '__main__':
	main()

t2 = datetime.datetime.now()
print ("\nCompleted at: ", t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1
print ("Processing time: " + str(tt),"\n")
