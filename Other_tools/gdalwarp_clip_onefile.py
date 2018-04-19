"""Clip a single raster in a folder with a specified shapefile"""

import os
import glob
import subprocess
import argparse


def get_files(indir: str, ext: str=".tif") -> list:
    """
    Return a list of full paths to the files in a directory that have the given extension
    :param indir: The full path to the directory containing the input rasters
    :param ext: The file extension, tif is the default
    :return:
    """
    return glob.glob(indir + os.sep + "*{}".format(ext))


def get_outdir(indir: str) -> str:
    """
    Get the full path to the output directory, create it if it doesn't already exist
    :param indir: The full path to the input directory
    :return:
    """
    outdir = os.path.split(indir)[0] + os.sep + "clip"

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    return outdir


def get_outfile(outdir: str, in_file: str, shp: str) -> str:
    """
    Get the full path to the output filename
    :param outdir: The full path to the output directory
    :param in_file: The full path to the current input raster file
    :param shp: The full path to the input shapefile
    :return:
    """
    return f"{outdir}{os.sep}{os.path.splitext(os.path.basename(in_file))[0]}_" \
           f"{os.path.splitext(os.path.basename(shp))[0]}.tif"


def do_clipping(in_f: str, out_f: str, shp: str) -> None:
    """
    Use gdalwarp to clip the input raster
    :param in_f: Full path to the input raster
    :param out_f: Full path to the output raster
    :param shp: Full path to the clipping shapefile
    :return:
    """
    subprocess.call([
        "gdalwarp",
        "-cutline",
        shp,
        "-crop_to_cutline",
        in_f,
        out_f
    ])

    return None


def main_work(in_rast: str, shp: str, outdir: str) -> None:
    """
    Perform clipping
    :param outdir: The full path to the output directory
    :param in_rast: The full path to the input raster to clip
    :param shp: The full path to the input shapefile used for clipping
    :return:
    """
    if os.path.exists(in_rast):

        if os.path.exists(shp):

            do_clipping(in_f=in_rast,
                        out_f=get_outfile(outdir=outdir,
                                          in_file=in_rast,
                                          shp=shp),
                        shp=shp)

        else:
            print("Couldn't find the specified shapefile")

    else:
        print("Could't find the specified raster file")

    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("-rast", dest="in_rast", type=str, required=True,
                        help="The full path to the input raster file to be clipped")

    parser.add_argument("-shp", dest="shp", type=str, required=True,
                        help="The full path to the .shp shapefile that will be used to clip the rasters")

    parser.add_argument("-o", dest="outdir", type=str, required=True,
                        help="The full path to the output directory")

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == "__main__":
    main()
