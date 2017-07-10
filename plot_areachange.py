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

import numpy as np

# from pprint import pprint

from osgeo import gdal

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

    b = np.bincount(srcdata) # retrieve count of unique values in srcdata array

    src, srcdata = None, None # close these datasets

    return b, a_unique

#%%
def get_plots(ind, b, outdir, tile, sum_b, y1, y2):

    """Purpose: Generate the Matplotlib bar plots.
    
    Args:
        ind = numpy array for the number of changes, used for the x-axis
        b = numpy array of the percent of tile for a given number of changes, used
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

    fig.suptitle("{} Area of Accumulated Change between {} and {}".format(tile, y1, y2),\
                 fontsize = 18, fontweight="bold")

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
            
            ax.text(rect.get_x() + rect.get_width()/2., label_position, 
                    "{:02.2f}%".format(height),
                    ha = "center", va="bottom", fontsize=8, rotation=45)
    
    autolabel(rects, ax)
    
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

    return None

#%%
def main():

    fromy, toy = None, None

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




