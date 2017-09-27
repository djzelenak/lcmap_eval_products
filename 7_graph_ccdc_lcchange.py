# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose: Generate vertical bar charts and tables of NLCD LC Change
for specific years.

"""

import os
import sys
import argparse

import matplotlib
import numpy as np
from osgeo import gdal

matplotlib.use("agg")
import matplotlib.pyplot as plt
from pandas import DataFrame


def get_rasters(indir):
    in_cl = []

    # in_cl = glob.glob(indir + os.sep + "*.tif")

    for root, folders, files in os.walk(indir):

        for folder in folders:

            for file in files:

                if file[-4:] == ".tif":
                    in_cl.append(os.path.join(root, folder) + os.sep + file)

    if in_cl is None:
        print("\n**Could not locate input LC Change files**\n")

        sys.exit(1)

    return in_cl


def read_data(cl):
    """
    Purpose: Open the Trends from-to LC Change .tif file.  
                Iterate through the list of from-to classes.
                Calculate the number of pixels for each from-to class.
                Call the get_trends_area function to calculate the total number
                of Trends pixels in the tile
    Args:
        cl = string, the full path to the Trends from-to .tif file
    
    Returns:
        classes = list, the Trends from-to classes
        masked_sum = list, the total number of pixels for each class
        total_pixels = the total number of Trends pixels in the tile             
    """

    cl_src = gdal.Open(cl, gdal.GA_ReadOnly)

    cl_data = cl_src.GetRasterBand(1).ReadAsArray()

    # list of original class values
    classes = [i for i in range(0, 10)]

    # list of all possible from/to combinations
    classmix = [str(i) + str(j) for i in classes for j in classes]

    # classes = np.unique(cl_data)

    masked_sum = []

    for ind, c in enumerate(classmix):

        mask_cl = np.copy(cl_data)

        if ind == 0:

            mask_cl[mask_cl != int(c)] = 111
            mask_cl[mask_cl == int(c)] = 1
            mask_cl[mask_cl == 111] = 0

        else:

            mask_cl[mask_cl != int(c)] = 0
            mask_cl[mask_cl == int(c)] = 1

        holder = np.sum(mask_cl)

        masked_sum.append(holder)

        # gives an idea of progress for the user
        print(c, " ", holder)

    cl_data, cl_src, mask_cl = None, None, None

    return classmix, masked_sum


def get_figure(label_set, df, tile, year1, year2, outname):
    """Purpose: Generate a matplotlib figure of n rows and 2 columns, the number
                rows is equal to the number of classes (label_set).  Column 1
                will contain vertical bar charts. Column 2 will contain tables
                showing the count and percent for row n 'from' class.
    Args:
        label_set = list, list of classes
        df = pandas DataFrame object contains class names, counts and percents
        tile = string, the name of the ARD tile
        year1, year2 = strings, the from and to years
        outname = the output path and filename for the .png image
    Returns:
        None
    """

    # RGB colors taken from Arc colormap and rescaled from 0-255 to 0-1
    """
    colors = {"0" : (0.0, 0.0, 0.0),
          "1" : (1.0, 0.0, 0.0),
          "2" : (1.0, 0.64705, 0.0),
          "3" : (1.0, 1.0, 0.0),
          "4" : (0.0, 0.5490, 0.0),
          "5" : (0.0, 0.0, 1.0),
          "6" : (0.0, 1.0, 1.0),
          "7" : (0.75, 0.75, 0.75),
          "8" : (0.3922, 0.3922, 0.3922),
          "9" : (1.0, 0.0, 1.0)}
    """

    # Generate figure with length(label_set) rows and 2 columns
    fig, axes = plt.subplots(nrows=len(label_set), ncols=2,
                             figsize=(16, 50))

    # Add figure title
    fig.text(0.5, .90, "%s CCDC %s to %s From-To Classes" % (tile, year1, year2),
             horizontalalignment="center", fontsize=22, fontweight='bold')

    print(label_set)
    for i, L in enumerate(label_set):

        t = []

        # iterate through rows of dataframe to retrieve values for class L
        for x in df.itertuples():

            if x[1][0] == L:
                t.append(x[1:])

        df_temp = DataFrame(t)

        # Assign column names
        df_temp.columns = ["Name", "Count", "Percent of Tile"]

        # generate bar charts in first column for class L in row i
        axes[i, 0].bar(df_temp.index, df_temp.Count, width=0.8)
        axes[i, 0].set_title('"From" Class ' + L + " Bar Chart")
        axes[i, 0].set_xticks(df_temp.index)
        axes[i, 0].set_xticklabels(df_temp.Name)
        axes[i, 0].set_xlabel("Class")
        axes[i, 0].set_ylabel("Count")

        # generate tables in second column for class L in row i
        axes[i, 1].table(cellText=df_temp.values, bbox=[0, 0, 1, 1], colLabels=df_temp.columns)
        axes[i, 1].set_title('"From" Class ' + L + " Table")
        axes[i, 1].set_xticks([])
        axes[i, 1].set_yticks([])

    # save the figure as a .png file
    plt.savefig(outname, bbox_inches="tight", dpi=150)

    return None


def usage():
    print("\n\t[-i the full path to the input raster file]\n"
          "\t[-o the full path to the output graph image (.png)]\n"
          "\t[-tile the tile name (used for graph title)]\n"
          "\t[-help display this message]\n")

    print("Example: python graph_ccdc_lcchange.py -i C:\... -o C:\... -tile h05v02 "
          "-frm 1992 -to 2011")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", type=str, required=True,
                        help="Full path to the directory containing all PyCCD LC Change products")

    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Full path to the output folder where the graphs will be saved")

    parser.add_argument("-t", "-tile", "--tile", type=str, required=True,
                        help="The name of the ARD tile.  This is only used for the graph title")

    args = parser.parse_args()

    out_dir = args.output

    in_dir = args.input

    tile = args.tile

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    in_files = get_rasters(in_dir)

    for in_cl in in_files:
        year1 = os.path.basename(in_cl)[-16:-12]

        year2 = os.path.basename(in_cl)[-10:-6]

        outname = "%s%s%s_ccdc%sto%s_lchange.png" % (out_dir, os.sep, tile, year1, year2)

        classes, class_sums = read_data(in_cl)

        # calculate the percent of the total for each from-to class
        class_perc = ["%.2f" % (val / 25000000.0 * 100.0) for val in class_sums]

        # convert the items in classes list to strings and save in a new list
        labels = [str(c) for c in classes]

        # get a set of the unique "from" classes (the first digit)
        labels_ = [l[0] for l in labels]
        label_set = set(labels_)  # converting to set removes duplicates
        label_set = list(label_set)  # convert back to list to allow indexing

        # Cluttered way to return a list of class values with the correct order
        label_set = [int(l) for l in label_set]
        label_set.sort()
        label_set = [str(l) for l in label_set]

        # create list of tuples to populate three data columns
        data = [(x, y, z) for x, y, z in zip(labels, class_sums, class_perc)]

        # create pandas dataframe from the list of tuples
        df = DataFrame(data)

        # add column names to the dataframe
        df.columns = ["Name", "Count", "Percent"]

        get_figure(label_set, df, tile, year1, year2, outname)

    return None


if __name__ == "__main__":
    main()
