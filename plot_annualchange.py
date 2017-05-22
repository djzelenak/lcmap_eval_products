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

from matplotlib.ticker import MaxNLocator

import numpy as np

from pprint import pprint

from osgeo import gdal

#%%
def get_rasters(indir):

    infiles = glob.glob(indir + os.sep + "*.tif")
    
    # r = infiles[-1] # test for now
    
    yearlist = []
    
    for r_i in infiles:
    
        temp_r = os.path.basename(r_i)
        yearlist.append( re.split("[_ .]", temp_r)[1] )
    
    # y = yearlist[-1] # test for now
    
    return infiles, yearlist

#%%
def get_data(r):
    
    src = gdal.Open(r, gdal.GA_ReadOnly)
    
    srcdata = src.GetRasterBand(1).ReadAsArray()
    
    # N = len(list(np.unique(srcdata)))
    
    a = np.copy(srcdata)
    
    a = a.flatten()
    
    # np.reshape(a, len(a))
    
    # a=np.squeeze(a)
    
    a[a > 0] = 1 # reclassify any change to value 1
    
    b = np.bincount(a) # retrieve count of unique values in a
    
    # b = np.delete(b, 0) # remove value 0
    
    # ind = np.nonzero(b)[0] # get index values (0...N-1)
    
    # ind = np.arange(len(b))
    
    src, srcdata, a = None, None, None # close these datasets
     
    return b

#%%
def get_plots(ind, b, outdir, labels):
    
    width= 0.8
    
    fig = plt.figure(figsize=(12,6))
    
    fig.suptitle("Annual Rates of Change", fontsize = 18, fontweight="bold")
    
    ax = fig.add_subplot(111)
    
    fig.subplots_adjust(top=0.85)
    
   # ax.set_title("Year {}".format(y))
    
    ax.set_xlabel("Year")
    ax.set_ylabel("% of Total Pixels Changed")
    
    ax.bar(ind-width/2., b)
    
    ax.xaxis.set_major_locator(MaxNLocator(len(labels)+1))
    
    ax.set_xticklabels(labels)
    
    plt.xticks(rotation = 90)
    
    # plt.xticks(np.arange(min(labels), max(labels)+1, 1.0))
    
    plt.xlim(0,len(labels))
    
    outgraph = outdir + os.sep + "annual_change.png"
    
    plt.savefig(outgraph, dpi=200, bbox_inches="tight")
    
    return None

#%%
def usage():
    
    print("\n\t[-i Full path to the input File Directory]\n" \
    "\t[-o Full path to the output location]\n" \
    "\t[-help Display this message]\n\n")

    print("\n\tExample: plot_annualchange.py -i C:/.../CCDCMap -from " + \
          "-o C:/.../graphs")

    print ""

    return None

#%%
def main():

    # fromyear, toyear = None, None
    
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

        elif arg == "-help":
            usage()
            sys.exit(1)

        i += 1
    
    if not os.path.exists(outfolder): os.mkdir(outfolder)

    rasters, years = get_rasters(infolder)
    
    years = [int(years[s]) for s in range(len(years))]
    
    label_years = np.array(years)
    
    ind = np.arange(len(years))
    
    bv = []
    
    p = 1
    for image in rasters:
        
        print "\nWorking on plot for image %s of %s"\
                %(str(p), str(len(rasters)))
        
        b = get_data(image)
        
        bv.append(b[1])
               
        p += 1
        
    for z in range(len(bv)):
        
        bv[z] = float(bv[z]) / 25000000.0 * 100.0
    
    b_vals = np.array(bv)

    get_plots(ind, b_vals, outfolder, label_years)    
    
    return None

#%%
if __name__ == "__main__":
    
    main()
    
        
        
        
        
