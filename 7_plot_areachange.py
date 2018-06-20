#!usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed May 17 13:44:42 2017
Last Updated on 9/14/2017 to work with annual thematic land cover in addition
to annual spectral change maps.

Create vertical bar charts that show the area of accumulated change.
Generate change accumulated between two specified years, or 1984 and 2015
by default.

@author: dzelenak
"""

import os
import glob
import argparse
import numpy as np
import matplotlib
matplotlib.use("agg")
import matplotlib.pyplot as plt
from osgeo import gdal


def get_rasters(indir, y1, y2, name):
    if name == "change":

        return glob.glob(indir + os.sep + "ccdc{}to{}ct.tif".format(y1, y2))[0]

    elif name == "cover":

        return glob.glob(indir + os.sep + "CoverPrim{}to{}ct.tif".format(y1, y2))[0]

    else:

        print("\n-type argument must either be 'change' or 'cover'\n")

    return None


def get_data(r):

    src = gdal.Open(r, gdal.GA_ReadOnly)

    srcdata = src.GetRasterBand(1).ReadAsArray()

    srcdata = srcdata.flatten()

    a_unique = np.arange(np.amax(srcdata) + 1)

    # retrieve count of unique values in srcdata array
    b = np.bincount(srcdata)

    return b, a_unique


def get_plots(ind, b, outdir, type_, tile, sum_b, y1, y2):
    """Purpose: Generate the Matplotlib bar plots.

    Args:
        ind = numpy array for the number of changes, used for the x-axis
        b = numpy array of the percent of tile for a given number of changes, used
            for the y-axis
        outdir = string, the full path to the output location where the graph
            will be saved as a .png file
        type_ = the product type (change or cover)
        tile = the ARD tile name, used for the title of the graph
        labels = list of integers, the years of observations used to label the
        x-axis ticks

    Return:
        None
    """

    fig = plt.figure(figsize=(12, 6))

    if type_ == "change":

        fig.suptitle("{} Area of Accumulated Spectral Change between {} and {}".format(tile, y1, y2),
                     fontsize=18, fontweight="bold")

    elif type_ == "cover":

        fig.suptitle("{} Area of Accumulated Cover Change between {} and {}".format(tile, y1, y2),
                     fontsize=18, fontweight="bold")

    ax = fig.add_subplot(111)

    fig.subplots_adjust(top=0.85)

    ax.set_title("{}% of the tile had at least 1 change".format(round(sum_b, 2)))

    ax.set_xlabel("Number of Changes")
    ax.set_ylabel("% of Tile")

    rects = ax.bar(ind, b, align="center")

    ax.set_xticks(np.arange(-1, len(ind)))

    plt.xlim(-0.5, len(ind))

    plt.ylim([0, max(b) * 1.1])

    def autolabel(rects, ax):

        (y_bottom, y_top) = ax.get_ylim()

        y_height = y_top - y_bottom

        for rect in rects:
            height = rect.get_height()

            label_position = height + (y_height * 0.01)

            ax.text(rect.get_x() + rect.get_width() / 2., label_position,
                    "{:02.2f}%".format(height),
                    ha="center", va="bottom", fontsize=8, rotation=45)

        return None

    autolabel(rects, ax)

    outgraph = outdir + os.sep + "area_change.png"

    plt.savefig(outgraph, dpi=200, bbox_inches="tight")

    return None


def main_work(indir, outdir, type_, tile, from_year="1984", to_year="2017"):

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    raster = get_rasters(indir, from_year, to_year, type_)

    b, ind = get_data(raster)

    bv = []

    for z in range(len(b)):
        bv.append(float(b[z]) / 25000000.0 * 100.0)

    sum_b = 0.00

    for p in range(1, len(bv)):
        sum_b = sum_b + bv[p]

    b_vals = np.array(bv)

    get_plots(ind, b_vals, outdir, type_, tile, sum_b, from_year, to_year)

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", dest="indir", type=str, required=True,
                        help="Full path to the input file directory")

    parser.add_argument("-o", dest="outdir", type=str, required=True,
                        help="Full path to the output directory")

    parser.add_argument("-type", dest="type_", type=str, choices=["change", "cover"], required=True,
                        help="Choose either cover or change product-type")

    parser.add_argument("-tile", dest="tile", type=str, required=True,
                        help="The tile name used for the figure title")

    parser.add_argument("-from", dest="from_year", type=str, required=False, default="1984",
                        help="The beginning year")

    parser.add_argument("-to", dest="to_year", type=str, required=False, default="2017",
                        help="The ending year")

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == "__main__":
    main()
