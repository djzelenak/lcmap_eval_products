#!usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed May 17 13:44:42 2017

Create vertical bar charts that show the annual rates of change.
Generate for all years in a single chart.

@author: dzelenak
"""
#%%
import os, sys, glob, re

import matplotlib.pyplot as plt

import numpy as np

# from pprint import pprint

from osgeo import gdal

#%%
def get_rasters(indir, y1, y2):

    if y1 is None: y1 = '1984'

    if y2 is None: y2 = '2015'

    infiles = glob.glob(indir + os.sep + "*.tif")

    yearlist = []

    for f in range(len(infiles)-1, -1, -1):

        temp_r = os.path.basename(infiles[f])

        temp_year = ( re.split("[_ .]", temp_r)[1] )

        if int(y2) < int(temp_year):

            del infiles[f]

        elif int(y1) > int(temp_year):

            del infiles[f]

        else:

            yearlist.append(temp_year)

    infiles.sort()

    yearlist.sort()

    return infiles, yearlist

#%%
def get_data(r):

    src = gdal.Open(r, gdal.GA_ReadOnly)

    srcdata = src.GetRasterBand(1).ReadAsArray()

    srcdata = srcdata.flatten()

    srcdata[srcdata > 0] = 1 # reclassify any change to value 1

    bins = np.bincount(srcdata) # retrieve count of unique values

    src, srcdata = None, None # close these datasets

    return bins

#%%
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
        
    fig = plt.figure(figsize=(12,6))

    fig.suptitle("{} Annual Rates of Change".format(tile), \
                 fontsize = 18, fontweight="bold")

    ax = fig.add_subplot(111)

    fig.subplots_adjust(top=0.85)

    ax.set_xlabel("Year")
    
    ax.set_xticks(np.arange(0, len(ind)))
    ax.set_xticklabels(labels)

    ax.set_ylabel("% of Tile")

    ax.bar(ind, b, align="center")

    plt.xticks(rotation = 90)

    plt.xlim(0,len(labels))

    outgraph = outdir + os.sep + "annual_change.png"

    plt.savefig(outgraph, dpi=200, bbox_inches="tight")

    return None

#%%
def usage():

    print("\n\t[-i Full path to the input File Directory]\n" \
    "\t[-o Full path to the output location]\n" \
    "\t[-frm The from year (1984 is default)]\n" \
    "\t[-to The to year (2015 is default)]\n" \
    "\t[-tile The tile name to be used for graph title]\n" \
    "\t[-help Display this message]\n")

    print("\n\tExample: plot_annualchange.py -i C:/.../CCDCMap -from " + \
          "-o C:/.../graphs\n")

    return None

#%%
def main():

    fromyear, toyear = None, None

    argv = sys.argv

    if len(argv) <= 1:
        print ("\n***Missing required arguments***")
        print ("Try -help\n")
        sys.exit(0)

    i = 1

    while i < len(argv):
        arg = argv[i]

        if arg == "-i":
            i = i + 1
            infolder = argv[i]

        elif arg == "-o":
            i = i + 1
            outfolder = argv[i]

        elif arg == "-tile":
            i = i + 1
            tile = argv[i]

        elif arg == "-frm":
            i = i + 1
            fromyear = argv[i]

        elif arg == "-to":
            i = i + 1
            toyear = argv[i]

        elif arg == "-help":
            usage()
            sys.exit(1)

        i += 1

    if not os.path.exists(outfolder): os.mkdir(outfolder)

    rasters, years = get_rasters(infolder, fromyear, toyear)

    # numpy array containing year values for the plot a-axis tick labels
    label_years = np.array([int(years[s]) for s in range(len(years))])

    # numpy array to be used for the plot x-axis tick marks
    ind = np.arange(len(years))

    bin_count_vals = []

    p = 1

    for image in rasters:

        print ("\nWorking on plot for image %s of %s"\
                %(str(p), str(len(rasters))) )

        bin_count = get_data(image)

        if len(bin_count) == 2:

            bin_count_vals.append(bin_count[1])

            p += 1

        else:

            ind = np.delete(ind, p-1)

            p += 1
    
    for num, bin_val in enumerate(bin_count_vals):

        # convert the counts to a percentage of the tile
        bin_count_vals[num] = float(bin_val) / 25000000.0 * 100.0

    # convert the list of bin count values to a numpy array for plotting
    b_vals = np.array(bin_count_vals)

    get_plots(ind, b_vals, outfolder, tile, label_years)

    return None

#%%
if __name__ == "__main__":

    main()
