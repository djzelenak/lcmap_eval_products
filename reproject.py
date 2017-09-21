import os
from osgeo import gdal
import glob
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", type=str, required=True, help="Full path to the input files")

args = parser.parse_args()

wkt = '''PROJCS["Albers",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378140,298.2569999999957,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433],AUTHORITY["EPSG","4326"]],PROJECTION["Albers_Conic_Equal_Area"],PARAMETER["standard_parallel_1",29.5],PARAMETER["standard_parallel_2",45.5],PARAMETER["latitude_of_center",23],PARAMETER["longitude_of_center",-96],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]'''

for dir, dirs, files in os.walk(args.input):

    for folder in dirs:

        file_list = glob.glob(os.path.join(dir, folder) + os.sep + "*.tif")

        for f in file_list:

            try:
            
                src = gdal.Open(f, gdal.GA_Update)
    
                src.SetProjection(wkt)
    
                src = None
                
            except: AttributeError
            