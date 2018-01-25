"""Get a list of all CoverPrim and SegmentChange maps, use specified tiles for Puget Sound eco-region, clip using
an eco-region level-3 boundary shapefile, merge tiles for each year."""

import datetime
import os
import subprocess
import argparse
import osr
import ogr
import gdal
import ast
from collections import namedtuple

BBox = namedtuple("BBox", ["left", "right", "top", "bottom"])


def get_time():
    """
    Return the current time
    :return:
    """
    return(datetime.datetime.now())


def get_raster_geoinfo(infile):
    """

    :param infile:
    :return:
    """
    src = gdal.Open(infile, gdal.GA_ReadOnly)

    gt = src.GetGeoTransform()

    srr = osr.SpatialReference()

    srr.ImportFromWkt(src.GetProjection())

    return gt, srr


def make_geotransform(srv, srr):
    """

    :param spatial_vector:
    :param spatial_raster:
    :return:
    """
    return osr.CoordinateTransformation(srv, srr)


def get_bounding_box(layer, raster_gt, coord_trans):
    """

    :param layer:
    :param raster_gt:
    :return:
    """
    layer.ResetReading()

    feature = layer.GetNextFeature()

    geom = feature.GetGeometryRef()

    geom.Transform(coord_trans)

    min_x, max_x, min_y, max_y = geom.GetEnvelope()

    left = min_x - (min_x - raster_gt[0]) % raster_gt[1]

    right = max_x + (raster_gt[1] - ((max_x - raster_gt[0]) % raster_gt[1]))

    bottom = min_y + (raster_gt[5] - ((min_y - raster_gt[3]) % raster_gt[5]))

    top = max_y - (max_y - raster_gt[3]) % raster_gt[5]

    return BBox(left=left, right=right, bottom=bottom, top=top)


def clip_and_mosaic(infiles, outdir, year, product, shp):
    """

    :param infiles:
    :param outdir:
    :param year:
    :param product:
    :param shp
    :return:
    """


    shp_src = ogr.Open(shp)

    layer = shp_src.GetLayer(0)

    srv = layer.GetSpatialRef()

    bboxes = []

    for f in infiles:

        gt, srr = get_raster_geoinfo(f)

        bbox = get_bounding_box(layer=layer, raster_gt=gt, coord_trans=make_geotransform(srv=srv, srr=srr))

        bboxes.append(bbox)

    left = min([box.left for box in bboxes])
    right = max([box.right for box in bboxes])
    top = max([box.top for box in bboxes])
    bottom = min([box.bottom for box in bboxes])

    mainbox = BBox(left=left, right=right, top=top, bottom=bottom)

    subprocess.call([
        "gdalwarp",
        "-cutline", shp,
        "-tr", str(abs(gt[1])), str(abs(gt[5])),
        "-te", str(mainbox.left), str(mainbox.bottom), str(mainbox.right), str(mainbox.top),
        [" %s " % f for f in infiles],
        "{outdir}{sep}puget_{year}_{product}.tif".format(outdir=outdir, sep=os.sep, year=year, product=product)
    ])

    return None

def main_work(indir, outdir, shp, ovr='False'):
    """

    :param indir:
    :param outdir:
    :return:
    """
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    ovr = ast.literal_eval(ovr)

    # List of ARD tiles
    # TODO Generate HV_list based on AOI envelope
    # HV_list = ['h03v01', 'h03v02', 'h03v03', 'h04v01', 'h04v02']
    HV_list = ["H03V01", "H03V02", "H03V03", "H04V01", "H04V02"]

    # List of years
    years = [str(y) for y in range(1984, 2016)]

    products = ['ChangeMap', 'LastChange', 'ChangeMagMap', 'QAMap', 'SegLength']

    for product in products:

        for year in years:

            infiles = []

            for hv in HV_list:

                # temp = "{indir}{sep}{hv}{sep}maps{sep}{hv}_{prod}_{y}.tif".format(indir=indir,
                #                                                                   sep=os.sep,
                #                                                                   hv=hv,
                #                                                                   prod=product,
                #                                                                   y=year)

                temp = "{indir}{sep}{hv}{sep}2017.06.20{sep}tif{sep}{prod}_{y}.tif".format(indir=indir,
                                                                                   sep=os.sep,
                                                                                   hv=hv,
                                                                                   prod=product,
                                                                                   y=year)

                infiles.append(temp)

            if not os.path.exists(outdir + os.sep + product):
                os.makedirs(outdir + os.sep + product)

            outfile = "{outdir}{sep}{product}{sep}puget_{year}_{product}.tif".format(outdir=outdir, sep=os.sep, year=year,
                                                                       product=product)

            file_exists = os.path.exists(outfile)

            if (file_exists and ovr) or not file_exists:
                print("Overwriting existing file")

                try:
                    os.remove(outfile)
                except:
                    pass

                clip_and_mosaic(infiles=infiles, outdir=outdir + os.sep + product, year=year, product=product, shp=shp)

            elif file_exists and not ovr:
                print("Not overwriting existing files")

                continue

    return None


def main():
    """

    :return:
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", dest="indir", type=str, required=True,
                        help="Full path to the directory containing the time-series mapped products")

    parser.add_argument("-o", "--output", dest="outdir", type=str, required=True,
                        help="Full path to the output location")

    parser.add_argument("-shp", "--shapefile", dest="shp", type=str, required=True,
                        help="Full path and filename of AOI shapefile")

    parser.add_argument("-ovr", dest="ovr", required=True, type=str, default='False',
                        help="Specify whether or not to overwrite existing outputs")

    # TODO make more customizable
    # parser.add_argument("-maps", "--maps", dest="products", type=str, nargs="*", default="CoverPrim", required=True,
    #                     choices=["CoverPrim", "CoverSec", "CoverConfPrim", "CoverConfSec", "QAMap",
    #                              "ChangeMap", "ChangeMagnitude", "SegLength", "SegChange",
    #                              "LastChange"],
    #                     help="Name of mapped product")
    #
    # parser.add_argument("-hv", "--hv", dest="hv_list", type=str, required=False, nargs="*",
    #                     default=,
    #                     help="A list of HV tiles to be included in the mosaic")
    #
    # parser.add_argument("-y", "--years", dest="years", type=str, required=False, nargs=2, default=(1984, 2015),
    #                     help="The beginning and end years")

    args = parser.parse_args()

    main_work(**vars(args))


if __name__ == "__main__":
    t1 = get_time()

    main()

    t2 = get_time()

    print("\nProcessing time: " + str(t2 - t1))