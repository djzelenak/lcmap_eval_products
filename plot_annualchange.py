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
# indir = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h05v02\ChangeMaps2\ChangeMagMap_color"

# outdir = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h05v02\graphs"

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
def get_rgba():

    # change "colormap" path as necessary
    # colormap = r"C:\....\color_changemag.txt"

    # 'hard-coded' color map copied directly from color_changemag.txt
    clr_list = ['<Entry c1="128" c2="25" c3="0" c4="255"/>',\
    '<Entry c1="143" c2="43" c3="0" c4="255"/>',\
    '<Entry c1="158" c2="58" c3="0" c4="255"/>',\
    '<Entry c1="173" c2="73" c3="2" c4="255"/>',\
    '<Entry c1="191" c2="94" c3="4" c4="255"/>',\
    '<Entry c1="207" c2="110" c3="6" c4="255"/>',\
    '<Entry c1="224" c2="131" c3="9" c4="255"/>',\
    '<Entry c1="240" c2="149" c3="12" c4="255"/>',\
    '<Entry c1="245" c2="161" c3="5" c4="255"/>',\
    '<Entry c1="247" c2="173" c3="0" c4="255"/>',\
    '<Entry c1="250" c2="183" c3="0" c4="255"/>',\
    '<Entry c1="252" c2="198" c3="0" c4="255"/>',\
    '<Entry c1="255" c2="213" c3="0" c4="255"/>',\
    '<Entry c1="255" c2="225" c3="0" c4="255"/>',\
    '<Entry c1="255" c2="242" c3="0" c4="255"/>',\
    '<Entry c1="255" c2="255" c3="0" c4="255"/>',\
    '<Entry c1="225" c2="255" c3="31" c4="255"/>',\
    '<Entry c1="191" c2="255" c3="54" c4="255"/>',\
    '<Entry c1="160" c2="255" c3="71" c4="255"/>',\
    '<Entry c1="133" c2="252" c3="93" c4="255"/>',\
    '<Entry c1="104" c2="247" c3="111" c4="255"/>',\
    '<Entry c1="78" c2="242" c3="132" c4="255"/>',\
    '<Entry c1="50" c2="237" c3="150" c4="255"/>',\
    '<Entry c1="0" c2="230" c3="168" c4="255"/>',\
    '<Entry c1="25" c2="212" c3="174" c4="255"/>',\
    '<Entry c1="35" c2="194" c3="186" c4="255"/>',\
    '<Entry c1="41" c2="176" c3="194" c4="255"/>',\
    '<Entry c1="40" c2="158" c3="201" c4="255"/>',\
    '<Entry c1="40" c2="141" c3="209" c4="255"/>',\
    '<Entry c1="35" c2="126" c3="217" c4="255"/>',\
    '<Entry c1="27" c2="108" c3="222" c4="255"/>',\
    '<Entry c1="0" c2="92" c3="230" c4="255"/>']

    # use the following code if reading colormap from a .txt file
    """
    clr_list = []

    with open(colormap, "r") as clr_txt:

        for line in clr_txt:

            clr_list.append(line)

    del clr_list[0]
    del clr_list[0]
    del clr_list[0]
    del clr_list[-1]
    """

    # create empty list object to contain rgba tuples
    rgba = []

    for i in range(len(clr_list)):

        r = re.split("[  .]", clr_list[i])[1][4:-1]
        r = (round( float(r) / 255.0, 2) )

        g = re.split("[  .]", clr_list[i])[2][4:-1]
        g = (round(float(g) / 255.0, 2) )

        b = re.split("[  .]", clr_list[i])[3][4:-1]
        b = (round(float(b) / 255.0, 2) )

        a = re.split("[  .]", clr_list[i])[4][4:-3]
        a = (float(a) / 255.0)

        rgba.append( (r, g, b, a) )

    # pprint(rgba)

    return rgba

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
    
    # infolder = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h05v02\ChangeMaps2\ChangeMap_color"

    # outfolder = r"C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h05v02\graphs"
    
    if not os.path.exists(outfolder): os.mkdir(outfolder)

    rasters, years = get_rasters(infolder)
    
    years = [int(years[s]) for s in range(len(years))]
    
    label_years = np.array(years)
    
    ind = np.arange(len(years))
    
    # colors = get_rgba()
    
    bv = []
    
    p = 1
    for image in rasters:
        
        print "\nWorking on plot for image %s of %s"\
                %(str(p), str(len(rasters)))
        
        b = get_data(image)
        
        bv.append(b[1])
        
        # get_plots(ind, b, image, years[p-1], outfolder)
        
        p += 1
        
    for z in range(len(bv)):
        
        bv[z] = float(bv[z]) / 25000000.0 * 100.0
    
    b_vals = np.array(bv)

    get_plots(ind, b_vals, outfolder, label_years)    
    
    return None

#%%
if __name__ == "__main__":
    
    main()
    
        
        
        
        