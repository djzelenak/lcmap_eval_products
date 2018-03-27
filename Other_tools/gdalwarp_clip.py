"""Clip all rasters in a folder with a specified shapefile"""

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


def get_outfile(outdir: str, in_file: str) -> str:
    """
    Get the full path to the output filename
    :param outdir: The full path to the output directory
    :param in_file: The full path to the current input raster file
    :return:
    """
    return outdir + os.sep + os.path.basename(in_file)


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


def main_work(indir: str, shp: str) -> None:
    """
    Parse through the input files, perform clipping
    :param indir: The full path to the directory containing the input rasters
    :param shp: The full path to the input shapefile used for clipping
    :return:
    """
    for f in get_files(indir=indir):

        do_clipping(in_f=f,
                    out_f=get_outfile(outdir=get_outdir(indir=indir),
                                      in_file=f),
                    shp=shp)

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", dest="indir", type=str, required=True,
                        help="The full path to the input directory that contains the rasters to be clipped")

    parser.add_argument("-shp", dest="shp", type=str, required=True,
                        help="The full path to the .shp shapefile that will be used to clip the rasters")

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == "__main__":
    main()
