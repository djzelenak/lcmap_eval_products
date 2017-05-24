#!usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed May 17 13:44:42 2017

Create vertical bar charts that show the area of accumulated change.
Generate change accumulated between two specified years, or 1984 and 2015 
by default.

@author: dzelenak
"""
#%%
import os, sys, glob #, re

import matplotlib.pyplot as plt

from matplotlib.ticker import MaxNLocator

import numpy as np

# from pprint import pprint

from osgeo import gdal

#%%
# indir = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h05v02\ChangeMaps2\ChangeMagMap_color"

# outdir = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h05v02\graphs"

#%%
def get_rasters(indir, y1, y2):

    infile = glob.glob(indir + os.sep + "ccdc{}to{}ct.tif".format(y1, y2))[0]

    return infile

#%%
def get_data(r):

    src = gdal.Open(r, gdal.GA_ReadOnly)

    srcdata = src.GetRasterBand(1).ReadAsArray()

    srcdata = srcdata.flatten()

    a_unique = np.arange(np.amax(srcdata) + 1)

    b = np.bincount(srcdata) # retrieve count of unique values in a

    src, srcdata = None, None # close these datasets

    return b, a_unique

#%%
def get_plots(ind, b, outdir, tile, sum_b, y1, y2):

    width= 0.8

    fig = plt.figure(figsize=(12,6))

    fig.suptitle("{} Area of Accumulated Change between {} and {}".format(tile, y1, y2),\
                 fontsize = 18, fontweight="bold")

    ax = fig.add_subplot(111)

    fig.subplots_adjust(top=0.85)

    ax.set_title("{}% of the tile had at least 1 change".format(round(sum_b, 2)))

    ax.set_xlabel("Number of Changes")
    ax.set_ylabel("% of Tile")

    ax.bar(ind-width/2., b)

    ax.xaxis.set_major_locator(MaxNLocator(len(ind)))

    plt.xlim(0,len(ind))

    outgraph = outdir + os.sep + "area_change.png"

    plt.savefig(outgraph, dpi=200, bbox_inches="tight")

    return None

#%%
def usage():

    print("\n\t[-i Full path to the input File Directory]\n" \
    "\t[-o Full path to the output location]\n" \
    "\t[-tile Name of ARD tile for the graph title]\n" \
    "\t[-help Display this message]\n\n")

    print("\n\tExample: plot_areachange.py -i C:/.../CCDCMap -from " + \
          "-o C:/.../graphs -tile h05v02")

    print ""

    return None

#%%
def main():

    fromy, toy = None, None

    argv = sys.argv

    if len(argv) <= 1:
        print "\n***Missing required arguments***"
        print "Try -help\n"
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

        elif arg == "-frm":
            i = i + 1
            fromy = argv[i]

        elif arg == "-to":
            i = i + 1
            toy = argv[i]

        elif arg == "-tile":
            i = i + 1
            tile = argv[i]

        elif arg == "-help":
            usage()
            sys.exit(1)

        i += 1

    if fromy == None or toy == None:
        
        fromy = '1984'
        
        toy = '2015'

    if not os.path.exists(outfolder): os.mkdir(outfolder)

    raster = get_rasters(infolder, fromy, toy)

    b, ind = get_data(raster)

    bv = []

    for z in range(len(b)):

        bv.append(float(b[z]) / 25000000.0 * 100.0)

    sum_b = 0.00

    for p in range(1, len(bv)):

        sum_b = sum_b + bv[p]

    b_vals = np.array(bv)

    get_plots(ind, b_vals, outfolder, tile, sum_b, fromy, toy)

    return None

#%%
if __name__ == "__main__":

    main()




