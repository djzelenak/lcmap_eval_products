'''
Subset annual layers from a multilayer raster to create individual rasters 
Author: Dan Zelenak
Based on script "Subset_Layers_v2.py" written by Devendra Dahal on 8/5/2015
Last Updated: 3/22/2017 by Dan Zelenak
'''

import os, sys, traceback, datetime, time, glob, subprocess, fnmatch, pprint
print sys.version
t1 = datetime.datetime.now()
print t1.strftime("%Y-%m-%d %H:%M:%S")

GDALpath = '/usr/bin'

def add_color_table(in_file, clr_table, Format):

	color_table = open(clr_table, 'r')

	# split the path and file name
	(dirName, fileName)                     = os.path.split(in_file)
	(fileBase, fileExt)                     = os.path.splitext(fileName)  
	
	out_vrt = r'%s/zzzzz%s_temp.vrt' % (dirName, fileBase)
		
	txt = open(in_file, 'r+')
	
	out_txt = open(out_vrt, 'w')
	
	# get lines in a list
	txt_read = txt.readlines()
	
	# check text for keywords
	key = '<VRTRasterBand dataType="%s" band="1">' % Format

	for line in txt_read:
		
		write = r'%s' % line
		
		out_txt.write(write)
		
		# insert color table following keywords
		if key in line:
			# print "\nFound the key!\n"
			
			color_read = color_table.readlines()
			
			for ln in color_read:
			
				out_txt.write(ln)
				
	out_txt.close()
	
	return out_vrt

def allCalc(InputDir, Type, FileFormat, OutputDir) :
	try:
		OutputDir = OutputDir + os.sep + Type
		
		if not os.path.exists(InputDir):
			#print "The input file location isn't valid, Please add the path\n"
			InputDir = raw_input("\nCan't find the specified input directory, please add the correct filepath : ")
		FileName = InputDir + os.sep + Type  #Type is either CoverDistMap or ChangeMap
		if not os.path.exists(FileName):
			print "\n---------\n",FileName,"\nThe File does not exists, Please check the data directory\n---------\n"
			sys.exit()
		if not os.path.exists(OutputDir):
			os.makedirs(OutputDir)
		print '\nFiles are saving in', OutputDir
		print '\n'	
		''' For now the CCDC has only 30 years of data (1985 to 2014) that's why it is hard coded 
		giving range from 1985 and 2014. When more year is added, we need to update this option'''
		for band, Year in zip(range(1,31),range(1985,2015)):
			
			print Year,
			if FileFormat == 'GRID':
				FileF = 'AAIGrid'
				bandFileFolder = OutputDir + os.sep + Type
				if not os.path.exists(bandFileFolder):
					os.makedirs(bandFileFolder)
				bandFile = bandFileFolder + os.sep + Type + 'Y' + str(Year) + ".asc"

			elif FileFormat == 'HFA':
				FileF =  'HFA'
				bandFile = OutputDir + os.sep + Type + "_" +str(Year) + ".img"				

			elif FileFormat == 'GTiff':
				FileF =  'GTiff'
				bandFile = OutputDir + os.sep + Type + "_" +str(Year) + ".tif"
			
			if not os.path.exists(bandFile):	
				
				if Type == 'CoverMap' or Type == 'CoverDistMap':
					clr_table = 'color_covermap.txt'
					###--------color_pallette--start here----------
					outcsv_File = r'%s/zzzzzz_%s_list.csv' % (OutputDir, Year)	
					if os.path.isfile(outcsv_File):
						os.remove(outcsv_File)
					
					outcsv2_File = open(outcsv_File, "wb")
					tempBandFile = OutputDir + os.sep + "zzzzz_" +str(Year) + ".tif"
					runsubset  = '%s/gdal_translate -of %s -b %s -q %s %s' % (GDALpath,FileF, str(band),FileName, tempBandFile) 			
					subprocess.call(runsubset, shell=True)		
					
					outcsv2_File.write(str(tempBandFile) + "\r\n")
					outcsv2_File.close()
					
					out_VRT =  OutputDir + os.sep +  "zzzz_" +str(Year) + ".vrt"
					com	= '%s/gdalbuildvrt -q -input_file_list %s %s' % (GDALpath,outcsv_File, out_VRT)
					subprocess.call(com, shell=True) 
					
					subprocess.call(com, shell=True) 
				
					out_vrt = add_color_table(out_VRT, clr_table, 'Byte')		
					runCom  = '%s/gdal_translate -of %s -q %s %s' % (GDALpath,FileF, out_vrt, bandFile)
					subprocess.call(runCom, shell=True)
				elif Type == 'ChangeMap':
					clr_table = 'color_changemap.txt'
					
					###--------color_pallette--start here----------
					outcsv_File = r'%s/zzzz_%s_list.csv' % (OutputDir, Year)	
					if os.path.isfile(outcsv_File):
						os.remove(outcsv_File)
					
					outcsv2_File = open(outcsv_File, "wb")
					tempBandFile = OutputDir + os.sep + "zzzzz_" +str(Year) + ".tif"
					runsubset  = 'gdal_translate -of %s -b %s -q %s %s' % (FileF, str(band),FileName, tempBandFile) 			
					subprocess.call(runsubset, shell=True)		
					
					outcsv2_File.write(str(tempBandFile) + "\r\n")
					outcsv2_File.close()
					
					out_VRT =  OutputDir + os.sep +  "zzzz_" +str(Year) + ".vrt"
					com	= '%s/gdalbuildvrt -q -input_file_list %s %s' % (GDALpath,outcsv_File, out_VRT)
					subprocess.call(com, shell=True) 
					
					subprocess.call(com, shell=True) 
					
					out_vrt = add_color_table(out_VRT, clr_table,'UInt16')		
					runCom  = '%s/gdal_translate -of %s -q %s %s' % (GDALpath,FileF, out_vrt, bandFile)
					subprocess.call(runCom, shell=True)
										
				else:
					runsubset  = '%s/gdal_translate -of %s -b %s -q %s %s' % (GDALpath,FileF, str(band),FileName, bandFile)	#-expand rgba 			
					subprocess.call(runsubset, shell=True)	
			
			for v in glob.glob(OutputDir + os.sep+ "zzz*"):
				os.remove(v)
		print "\n\nAll done"
	except:
		print "Dang!! Something terrible happened.."
		print traceback.format_exc()

	
def usage():
	print ''
	print('[-i Input File Directory]\n \
	[-type Input File name (root only, e.g. ChangeMap)]\n \
	[-of outfile format (3 formats supported: GTiff, HFA, and GRID)]\n \
	[-o Output Folder with complete path]\n\n')
	print ''
	
def examps():
	print ''
	print('Usage: python 1_subset_layers.py -i /.../CCDCMap -type CoverDistMap -of GTiff -o /Some/Directory\n')
	print ''

def main():
			
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
			inputdir         = argv[i]
			
		elif arg == '-type':
			i           = i + 1
			dtype      = argv[i]     

		elif arg == '-of':
			i           = i + 1
			oformat      = argv[i]       

		elif arg == '-o':
			i           = i + 1
			outputdir         = argv[i] 

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
	
	# Call the primary function
	allCalc(inputdir, dtype, oformat, outputdir)

if __name__ == '__main__':
	main()	

t2 = datetime.datetime.now()
print t2.strftime("%Y-%m-%d %H:%M:%S")
tt = t2 - t1
print "\tProcessing time: " + str(tt) 
