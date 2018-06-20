#!usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed May 17 13:44:42 2017

Create vertical bar charts that show the annual rates of change.
Generate for all years in a single chart.

@author: dzelenak
"""
import os
import glob
import re
import argparse
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from osgeo import gdal


def get_rasters(indir, y1='1984', y2='2017'):

    infiles = glob.glob(indir + os.sep + "*.tif")

    yearlist = []

    for f in range(len(infiles) - 1, -1, -1):

        temp_r = os.path.basename(infiles[f])

        temp_year = (re.split("[_ .]", temp_r)[1])

        if int(y2) < int(temp_year):

            del infiles[f]

        elif int(y1) > int(temp_year):

            del infiles[f]

        else:

            yearlist.append(temp_year)

    infiles.sort()

    yearlist.sort()

    return infiles, yearlist


def get_data(r):
    src = gdal.Open(r, gdal.GA_ReadOnly)

    srcdata = src.GetRasterBand(1).ReadAsArray()

    srcdata = srcdata.flatten()

    srcdata[srcdata > 0] = 1  # reclassify any change to value 1

    bins = np.bincount(srcdata)  # retrieve count of unique values

    return bins


def get_plots(ind, b, outdir, tile, labels):
    """Purpose: Generate the Matplotlib bar plots.
    
    Args:
        ind = numpy array of the years for observations, used for the x-axis
        b = numpy array of the percent of observations for a given year, used
            for the y-axis
        outdir = string, the full path to the output location where the graph
            will be saved as a .png file
        tile = the ARD tile name, used for the title of the graph
        labels = list of integers, the years of observations used to label the
        x-axis ticks
    
    Return:
        None
    """

    fig = plt.figure(figsize=(12, 6))

    fig.suptitle("{} Annual Rates of Change".format(tile),
                 fontsize=18, fontweight="bold")

    ax = fig.add_subplot(111)

    fig.subplots_adjust(top=0.85)

    ax.set_xlabel("Year")

    ax.set_xticks(np.arange(0, len(ind)))

    ax.set_xticklabels(labels)

    ax.set_ylabel("% of Tile")

    rects = ax.bar(ind, b, align="center")

    plt.xticks(rotation=90)

    plt.xlim([-0.5, len(labels)])

    plt.ylim([0, max(b) * 1.1])

    def autolabel(rects_, ax_):
        (y_bottom, y_top) = ax_.get_ylim()

        y_height = y_top - y_bottom

        for rect in rects_:
            height = rect.get_height()

            label_position = height + (y_height * 0.01)

            ax_.text(rect.get_x() + rect.get_width() / 2., label_position,
                     "{:02.2f}%".format(height),
                     ha="center", va="bottom", fontsize=8, rotation=65)

        return None

    autolabel(rects, ax)

    outgraph = outdir + os.sep + "annual_change.png"

    plt.savefig(outgraph, dpi=200, bbox_inches="tight")

    return None


def main_work(indir, outdir, tile, from_year, to_year):
    pass

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    rasters, years = get_rasters(indir, from_year, to_year)

    label_years = np.array([int(years[s]) for s in range(len(years))])

    # numpy array to be used for the plot x-axis tick marks
    ind = np.arange(len(years))

    bin_count_vals = list()

    for c, image in enumerate(rasters):

        print("\nWorking on plot for image %s of %s" % (c + 1, len(rasters)))

        bin_count = get_data(image)

        if len(bin_count) == 2:

            # bin_count[0] = number of 0-value pixels
            # bin_count[1] = number of recoded 1-value pixels
            bin_count_vals.append(bin_count[1])

            # p += 1

        else:
            # case where the entire tile is 0
            bin_count_vals.append(0)

    for num, bin_val in enumerate(bin_count_vals):
        # convert the counts to a percentage of the tile
        bin_count_vals[num] = float(bin_val) / 25000000.0 * 100.0

    # convert the list of bin count values to a numpy array for plotting
    b_vals = np.array(bin_count_vals)

    get_plots(ind, b_vals, outdir, tile, label_years)

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", dest="indir", type=str, required=True,
                        help="Full path to the input file directory")

    parser.add_argument("-o", dest="outdir", type=str, required=True,
                        help="Full path to the output location")

    parser.add_argument("-tile", dest="tile", type=str, required=True,
                        help="The name of the tile, used for the figure title")

    parser.add_argument("-from", dest="from_year", type=str, required=False, default='1984',
                        help="The beginning year")

    parser.add_argument("-to", dest="to_year", type=str, required=False, default='2017',
                        help="The ending year")

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == "__main__":
    main()
