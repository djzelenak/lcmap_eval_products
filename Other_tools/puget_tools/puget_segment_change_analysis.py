# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose: Generate confusion matrix to perform analysis of from-to class destination based on the
         Segment Change mapped products.

Horizontal Axis = Destination classes
Vertical Axis = Origin classes

"""

import argparse
import datetime
import glob
import os
import sys
import traceback
import matplotlib
import pickle

matplotlib.use("agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
# from matplotlib import colors as clr

import numpy as np
import pandas as pd
from osgeo import gdal

gdal.UseExceptions()
gdal.AllRegister()

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S\n"))

# pickle_file = "Other_tools%spuget_tools%spuget_mask.pickle" % (os.sep, os.sep)
pickle_file = "/lcmap_data/dzelenak/puget/puget_mask.pickle"

with open(pickle_file, "rb") as p:
    MASK = pickle.load(p)

# Get the total number of pixels in the eco_region mosaic
TOTAL = np.bincount(MASK.flatten())[1]

# RGB class colors
colors = [(0.0, 0.0, 0.0),
          (1.0, .188235, 0.078431),
          (0.980392, 0.588235, 0.180392),
          (0.941176, 0.960784, 0.34902),
          (0.0, 0.560784314, 0.0),
          (0.211765, 0.290196, 1.0),
          (0.2, 0.803922, 0.588235),
          (0.882353, 0.882353, 0.882353),
          (0.509804, 0.509804, 0.509804),
          (0.494, 0.0784, 1.0)]

# List of class values
classes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def error_message(file):
    """
    Print information about the error without raising an exception
    :param file: The current file being worked on
    :type file: str
    :return:
    """
    print(f"\nSkipping file {file}")
    print("\nType of Exception: ", sys.exc_info()[0])
    print("\nException Value: ", sys.exc_info()[1])
    print("\nTraceback Info: \n")
    traceback.print_tb(sys.exc_info()[2])

    return None


def get_files(path, lookfor, years=None):
    """
    Use glob to generate a list of all matching files in the specified path
    :param path: Full path to the location of the From-To layers
    :type path: str
    :param year: Year to look for in the file names
    :type year: str
    :param lookfor: Layer type to look for
    :type lookfor: str
    :return: List of paths
    :rtype: list
    """
    # All files in path ending in .tif
    filelist = glob.glob(f"{path}{os.sep}*_{lookfor}*.tif")

    filelist.sort()

    if len(filelist) == 0:
        print("\nCould not locate any files {}\n".format(path))

        sys.exit(1)

    if years is None:
        return filelist

    else:
        return [f for f in filelist for y in years if y in f]


def read_data(infile):
    """
    Load raster data into an array
    :param infile: The full path to the input raster
    :type infile: str
    :return: Array object
    :rtype: numpy.ndarray
    """
    return gdal.Open(infile, gdal.GA_ReadOnly).ReadAsArray()


def get_tile(infile):
    """
    Get the name of the H-V tile by looking at one of the files in the file list
    :param infile: The file to look at
    :type infile: str
    :return: The tile name (e.g. H25V42)
    :rtype: str
    """
    looking = infile.split(sep=os.sep)

    L = ""

    for l in looking:
        if ("h" in l or "H" in l) and ("v" in l or "V" in l):
            L = l
            break

    try:
        tile = L.split(sep="_")[1]
    except IndexError:
        tile = L

    return tile.upper()


def get_fname(infile):
    """
    Generate a string representing the output base file name
    :param infile: Full path to the input raster
    :type infile: str
    :return: Output base name, the current year, and the tile name
    :rtype: str, str, str
    """
    basename = os.path.splitext(os.path.basename(infile))[0]

    # return basename, basename[-4:]
    return basename, basename.split("_")[1]


def get_cover_table(indata):
    """
    Create pandas DataFrames from the thematic land cover product
    :param indata:
    :return:
    """
    val_counts = np.bincount(indata.flatten())

    total = np.sum(val_counts)

    val_percents = np.zeros_like(val_counts, dtype=np.float)

    for ind, v in enumerate(val_counts):
        val_percents[ind] = round(v / total * 100.0, 2)

    df_count = pd.DataFrame(val_counts, columns=["Count"])

    df_perc = pd.DataFrame(val_percents, columns=["Percent"])

    return df_count, df_perc


def compute_confusion_matrix(fromto, f):
    """
    Calculate the confusion matrix for the current from-to data set
    :param fromto: An array object containing the from-to data
    :type fromto: numpy.ndarray
    :return:
    """
    from_vals = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    to_vals = [0, 1, 2, 3, 4, 5, 6, 7, 8]

    # Used for keeping track of progress for the current cnf matrix calculation
    total = float(len(from_vals) * len(to_vals))

    # Get the unique values present in the SegmentChange data
    check_vals = np.unique(fromto)

    # create the confusion matrix, for now containing all zeros
    confusion_matrix = np.zeros((len(from_vals), len(to_vals)), np.int32)

    print(f"\ngenerating {len(to_vals)} by {len(from_vals)} confusion matrix for file {f}")

    counter = 1.0

    # loop through columns
    for c in from_vals:

        # loop through rows
        for r in to_vals:
            # val is concatenated from + to values
            val = int(str(c) + str(r))

            # Keep track of the progress relative to the number of total from-to combinations
            current = counter / total * 100.0  # as percent

            if val in check_vals and val != 0:
                # (c, r) means 'from' is vertical axis and 'to' is the horizontal axis
                confusion_matrix[to_vals.index(c), from_vals.index(r)] = np.bincount(fromto.flatten())[val]

            else:
                confusion_matrix[to_vals.index(c), from_vals.index(r)] = 0

            # show the percent complete
            sys.stdout.write("\r%s%% Done " % str(current)[:5])

            # needed to display the current percent complete
            sys.stdout.flush()

            counter += 1.0

        sys.stdout.flush()

    # add row totals in a new column at the end
    x_sum = confusion_matrix.sum(axis=1)

    x_sum = np.reshape(x_sum, (len(from_vals), 1))

    confusion_matrix = np.append(arr=confusion_matrix, values=x_sum, axis=1)

    # add column totals in a new row at the end
    y_sum = confusion_matrix.sum(axis=0)

    y_sum = np.reshape(y_sum, (1, len(to_vals) + 1))

    confusion_matrix = np.append(arr=confusion_matrix, values=y_sum, axis=0)

    # insert a blank row and column at the top/left to contain class values
    confusion_matrix = np.insert(arr=confusion_matrix, obj=0, values=0, axis=0)

    confusion_matrix = np.insert(arr=confusion_matrix, obj=0, values=0, axis=1)

    # Append 0's so len(classes) matches the new shape of the confusion matrix
    from_vals.insert(0, 0)
    to_vals.insert(0, 0)

    # Append 99999999 instead of 'total' because can't have strings in array of numbers
    from_vals.append(99999999)
    to_vals.append(99999999)

    # insert the class names into the blank columns/rows of the matrix
    for c in range(len(from_vals)):
        confusion_matrix[c, 0] = from_vals[c]

        confusion_matrix[0, c] = to_vals[c]

    return confusion_matrix


def write_to_csv(matrix, outdir, name, lookfor="99999999"):
    """

    :param matrix:
    :param outdir:
    :param name:
    :param lookfor:
    :return:
    """

    # If for some reason the temporary .csv already exists, remove it
    if os.path.exists('%s/%s.csv' % (outdir, lookfor)):
        os.remove('%s/%s.csv' % (outdir, lookfor))

    # save the confusion matrix to a temporary .csv file named 999999.csv
    np.savetxt('%s/%s.csv' % (outdir, lookfor), matrix, fmt='%d')

    # open the temp .csv file and a new final output csv file named with the fname variable
    with open('%s/%s.csv' % (outdir, lookfor), 'r') as f:
        text = f.read()

        text = text.replace(lookfor, 'Total')

    with open('%s/%s.csv' % (outdir, name), 'w') as out:
        out.write(text)

    for root, folders, files in os.walk(outdir):
        for x in files:
            if x == '99999999.csv':
                os.remove(os.path.join(root, x))

    return None


def array_to_dataframe(matrix):
    """

    :param matrix:
    :return:
    """
    df = pd.DataFrame(matrix[1:, 1:], index=matrix[1:, 0], columns=matrix[0, 1:])

    # Find and replace 99999999 with "Total"
    try:

        # Find in dataframe index
        ind_list = df.index.tolist()

        idx = ind_list.index(99999999)

        ind_list[idx] = "Total"

        df.index = ind_list

        # Find in dataframe columns
        col_list = df.columns.tolist()

        idx = col_list.index(99999999)

        col_list[idx] = "Total"

        df.columns = col_list

    except ValueError:
        pass

    return df


def write_to_excel(writer, df_seg, df_cover, df_cover_perc, df_summary, year):
    """

    :param writer:
    :param df_seg:
    :param df_cover:
    :param df_cover_perc:
    :param year:
    :return:
    """
    # Get a list of the diagonal values from the confusion matrix
    diags = [df_seg.loc[i[0], j[0]] for i in df_seg.iterrows() for j in df_seg.iteritems() if i[0] == j[0]]

    df_cover_perc.columns = ["% Tile"]

    df_cover_area = df_cover * 0.0009

    df_cover_area.columns = ["Area"]

    workbook = writer.book

    worksheet = workbook.add_worksheet(year)

    writer.sheets[year] = worksheet

    # Create some formats to use for writing to the excel worksheet
    format = workbook.add_format({"bold": True})
    diag_format = workbook.add_format({"bold": True, "bg_color": "#C0C0C0", "border_color": "#000000"})

    # Convert the dataframes to XLsxWriter Excel objects
    df_seg.to_excel(writer, sheet_name=year, startrow=2, startcol=1)

    df_cover.to_excel(writer, sheet_name=year, startrow=16, startcol=1)

    df_cover_area.to_excel(writer, sheet_name=year, index=False, startrow=16, startcol=3)

    df_cover_perc.to_excel(writer, index=False, sheet_name=year, startrow=16, startcol=4)

    df_summary.to_excel(writer, sheet_name=year, startrow=16, startcol=7)

    # Add row and column names
    worksheet.write(0, 5, "Segment Break Class From-To Distribution", format)
    worksheet.write(1, 6, "Destination", format)
    worksheet.write(6, 0, "Origin", format)
    worksheet.write(15, 2, "Total Class Distribution", format)
    worksheet.write(15, 8, "Segment Break Class Summary", format)

    # Format the diagonal cells where from class = to class, write the values to the worksheet
    worksheet.write("C4", diags[0], diag_format)
    worksheet.write("D5", diags[1], diag_format)
    worksheet.write("E6", diags[2], diag_format)
    worksheet.write("F7", diags[3], diag_format)
    worksheet.write("G8", diags[4], diag_format)
    worksheet.write("H9", diags[5], diag_format)
    worksheet.write("I10", diags[6], diag_format)
    worksheet.write("J11", diags[7], diag_format)
    worksheet.write("K12", diags[8], diag_format)
    worksheet.write("L13", diags[9], diag_format)

    return None


def get_fromclass_percents(table):
    """
    Create a pandas DataFrame from the table that contains the percent of each value within a
    given row (i.e. originating class)
    :param table: <pandas.core.frame.DataFrame>
    :return: <pandas.core.frame.DataFrame>
    """
    percents = table.iloc[table.index != "Total"]

    percents = table[[0, 1, 2, 3, 4, 5, 6, 7, 8]].copy()

    return percents.div(percents.sum(1) / 100, 0)


def get_class_totals(matrix):
    """
    First slice the matrix to get all rows of the last column.  Then, remove the first row from this slice because
    it is just a column header value.  Also, don't include the last element because this is the overall total
    :param matrix: The from-to counts array
    :return: The column from the from-to array containing class totals
    :rtype: numpy.ndarray
    """
    return matrix[:, -1][1:-1]


def get_segments_total(matrix):
    """
    Get the total number of segment changes for the current year from the from-to array.  This value is already
    stored in the from-to array in the last row and column which represent the overall total
    :param matrix: The from-to data array
    :return: The sum of all segment changes for the current year
    :rtype: int
    """
    return matrix[-1, -1]


def get_thematic_change_percent(matrix):
    """
    Calculate the percent of the tile that underwent thematic change for the given year.  This means that there was
    a segment change and that the originating class ended up as a different class in the new segment.
    :param matrix: The from-to data array
    :type matrix: numpy.ndarray
    :return: The percentage of the tile that underwent thematic change
    :rtype: float
    """
    # Slice out the from-to counts from the array removing the row/column names and row/column totals
    counts = matrix[1:10, 1:10]

    # Create an array of zeros that will contain each row's total of thematic change
    thematic_count = np.zeros(9, dtype=np.int)

    for ind, i in enumerate(counts):
        # Create a copy of the ith row of counts
        temp = np.copy(i)

        # Use ind to identify counts associated with static class across segment change, set this element to equal 0
        # so that it is not included in the sum
        temp[ind] = 0

        # Store the sum of the thematic changes in row i in the thematic_count array, but don't include counts for a
        # class -> 0 as cover change.
        thematic_count[ind] = np.sum(temp[1:])

    # Calculate the sum of all row totals
    total_count = np.sum(thematic_count)

    return total_count / TOTAL * 100.0


def get_seg_change_plots(seg_matrix, seg_table, cover_matrix, tile, year, out_img):
    """
    Generate annual segment change plots
    :param seg_matrix:
    :param seg_table:
    :param cover_matrix:
    :param tile:
    :param year:
    :param out_img:
    :return:
    """
    def autolabel(rects, ax, totals):
        """
        Generate labels for the horizontal bar plot.  Use the class totals as the label values
        :param rects:
        :param ax:
        :param totals:
        :return:
        """

        for ind, rect in enumerate(rects):
            width = int(rect.get_width())

            """
            if width < 50:
                xloc = width + 5
                clr = "k"
                align = "right"
            else:
                xloc = 0.98 * width
                clr = "k"
                align = "left"
            """
            xloc = 100

            clr = "k"

            align = "left"

            yloc = rect.get_y() + rect.get_height() / 2.0

            # Calculate the percent of the class that changed
            if not totals[1][ind] == 0:
                perc = round(totals[0][ind] / totals[1][ind] * 100.0, 2)
            else:
                perc = 0.00

            label = ax.text(xloc, yloc, "{:02.2f} $km^2$ | {:02.2f}%".format(totals[0][ind], perc),
                            ha=align, va="center",
                            color=clr, weight="bold",
                            clip_on=True, fontsize=8)

        return None

    tile = "Puget"

    df_class_percents = get_fromclass_percents(seg_table)

    # Needed to use the .astype(np.int64) to avoid value overflow warning
    seg_class_totals = (get_class_totals(seg_matrix)).astype(np.int64)

    # seg_class_areas = [round(class_total * 900 * .0009, 2) for class_total in seg_class_totals]
    seg_class_areas = [round(class_total * .0009, 2) for class_total in seg_class_totals]

    segments_total = get_segments_total(seg_matrix)

    class_segment_proportions = [class_total / segments_total * 100.0 for class_total in seg_class_totals]

    total_thematic_percent = get_thematic_change_percent(seg_matrix)

    total_segment_percent = segments_total / TOTAL * 100.0

    cover_areas = [round(cover * .0009, 2) for cover in cover_matrix]

    plt.style.use("ggplot")

    if os.path.exists(out_img):
        return seg_class_areas, cover_areas, \
           [round(s / c * 100.0, 2) if c != 0 else 0.00 for s, c in zip(seg_class_areas, cover_areas)], segments_total

    # Create the figure with two subplots that share a y-axis
    fig, (ax1, ax2) = plt.subplots(figsize=(16, 5), dpi=200, nrows=1, ncols=2, sharex=False, sharey=False)

    # Use the DataFrame class_percents to plot the proportion of change in each originating class on the right axis
    df_class_percents[:-1].plot.barh(stacked=True, color=colors[:-1], ax=ax2, edgecolor="k", width=0.5, legend=False)

    # Share the y-axis between ax1 and ax2, but not ax3
    ax1.get_shared_y_axes().join(ax1, ax2)

    # Use array class_segment_proportions to plot the proportion of each class to the segments total
    seg_rects = ax1.barh(np.arange(len(class_segment_proportions)), class_segment_proportions,
                         color=colors[:-1], height=0.5, edgecolor="k")

    # Add class total labels to the horizontal bars
    autolabel(rects=seg_rects, ax=ax1, totals=(seg_class_areas, cover_areas))

    # Plot the first class at the top, this inverts the y-axis for both subplots because they share y
    ax1.invert_yaxis()

    # Invert the x-axis on the left subplot so that it matches the origin of the right subplot
    ax1.invert_xaxis()

    # Add figure title and subtitles
    fig.suptitle(f"{tile} {year}", fontsize=18, y=1.10)
    plt.figtext(0.5, 1.01, f"Segment Change in {round(total_segment_percent, 2)}% of Tile", fontsize=12, ha="center")
    plt.figtext(0.5, 0.96, f"Cover Change in {round(total_thematic_percent, 2)}% of Tile", fontsize=12, ha="center")

    # Add subplot titles
    ax1.set_title("Percent of Origin Class in All Segment Breaks\nArea with Segment Break | "
                  "Percent of Class with Segment Break",
                  fontsize=12)

    ax2.set_title("Percent of Class Destination from Origin Class", fontsize=12)

    # Add axes labels and titles
    ax1.set_xlabel("Percent", fontsize=12)
    ax2.set_xlabel("Percent", fontsize=12)
    ax1.set_yticklabels([""] * len(np.arange(9)))
    ax1.set_yticks(np.arange(len(class_segment_proportions)))
    ax2.get_yaxis().set_visible(False)

    # Set x-limit on the left subplot so that all figures have the same window scale
    ax1.set_xlim(right=0, left=105)
    ax2.set_xlim(left=0, right=105)

    # Create the legend manually
    no_label = mpatches.Patch(color=colors[0], label="0 - Insufficient Data")
    dev_label = mpatches.Patch(color=colors[1], label="1 - Developed")
    ag_label = mpatches.Patch(color=colors[2], label="2 - Agriculture")
    grass_label = mpatches.Patch(color=colors[3], label="3 - Grassland/Shrubland")
    tree_label = mpatches.Patch(color=colors[4], label="4 - Tree Cover")
    water_label = mpatches.Patch(color=colors[5], label="5 - Water")
    wet_label = mpatches.Patch(color=colors[6], label="6 - Wetland")
    ice_label = mpatches.Patch(color=colors[7], label="7 - Ice/Snow")
    bar_label = mpatches.Patch(color=colors[8], label="8 - Barren")

    handles = [no_label, dev_label, ag_label, grass_label, tree_label, water_label, wet_label, ice_label, bar_label]

    # Display the legend to the left subplot and mimic the lef subplot y-axis with its placement
    ax1.legend(handles=handles, loc="upper right", bbox_to_anchor=(0, 0.98), ncol=1, labelspacing=1.83,
               markerfirst=False, facecolor="w", frameon=False)

    # Adjust subplots to make enough room at the top for figure titles
    fig.subplots_adjust(top=0.85)

    # Adjust subplots so that there is no space between the y-axes
    fig.subplots_adjust(wspace=0)

    plt.savefig(out_img, dpi=200, bbox_inches="tight")

    plt.close()

    return seg_class_areas, cover_areas, \
           [round(s / c * 100.0, 2) if c != 0 else 0.00 for s, c in zip(seg_class_areas, cover_areas)], segments_total


def get_summary_plot(froms, tos, tile, out_img):
    """

    :param froms:
    :param tos:
    :param tile:
    :param out_img:
    :return:
    """
    tile = "Puget Eco-region"

    if os.path.exists(out_img):
        return None

    fig, axes = plt.subplots(figsize=(15, 20), dpi=200, nrows=2, ncols=2, sharex=False, sharey=False)

    froms[1].T.iloc[:, :].plot.barh(stacked=True, color=colors[:-1], legend=False, width=0.8, ylim=(1984, 2014),
                                    yticks=np.arange(1984, 2015), title="Originating Class Percentage Through Time",
                                    ax=axes[0, 0], edgecolor="k")

    froms[0].T.iloc[:, :].plot.barh(stacked=True, color=colors[:-1], legend=True, width=0.8, ylim=(1984, 2014),
                                    yticks=np.arange(1984, 2015), title="Originating Class Quantity Through Time",
                                    ax=axes[0, 1], edgecolor="k")

    tos[1].T.iloc[:, :].plot.barh(stacked=True, color=colors[:-1], legend=False, width=0.8, ylim=(1984, 2014),
                                  yticks=np.arange(1984, 2015), title="Destination Class Percentage Through Time",
                                  ax=axes[1, 0], edgecolor="k")

    tos[0].T.iloc[:, :].plot.barh(stacked=True, color=colors[:-1], legend=True, width=0.8, ylim=(1984, 2014),
                                  yticks=np.arange(1984, 2015), title="Destination Class Quantity Through Time",
                                  ax=axes[1, 1], edgecolor="k")

    fig.suptitle(f"Annual Segment Change for Tile {tile}", fontsize=24)

    # Adjust subplots to make enough room at the top for figure titles
    fig.subplots_adjust(top=0.92, hspace=0.15, wspace=0.1)

    plt.savefig(out_img, dpi=200, bbox_inches="tight")

    plt.close()

    return None


def get_annual_class_plot(sum_class, sum_class_seg, tile, out_img):
    """
    Generate a plot showing the class quantities across time overlaid with the quantities of each class that had
    segment change
    :param sum_class:
    :param sum_class_seg:
    :param tile:
    :param out_img:
    :return:
    """
    tile = "Puget Eco-Region"

    fig, axes = plt.subplots(figsize=(12, len(classes) * 5), dpi=100, nrows=len(classes), ncols=1,
                             sharex=False, sharey=False)

    for ind, ax in enumerate(axes):
        # Plot the class totals
        ax.bar(np.arange(1984, 2016), [sum_class[k][ind] for k in sum_class.keys()], color=colors[ind], edgecolor="k")

        # Plot the totals of each class with segment change
        ax.bar(np.arange(1984, 2016), [sum_class_seg[k][ind] if not ax == axes[-1] else 0
                                       for k in sum_class_seg.keys()],
                         color="white", alpha=0.7, edgecolor="k")

        ax.set_title(f"Quantity of Class {ind} per Year")

    fig.suptitle("Overall Class Quantity Overlaid with Quantity of Seg Change", y=1.01, fontsize=22)

    plt.figtext(0.5, 1.0, f"{tile}", fontsize=18, ha="center")

    fig.subplots_adjust(top=0.99)

    plt.savefig(out_img, dpi=200, bbox_inches="tight")

    return None


def main_work(indir, outdir, years=None, overwrite=False):
    """

    :param indir:
    :param outdir:
    :param years:
    :param overwrite:
    :return:
    """
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # Get list of the segment change files
    seg_files = get_files(path=indir, years=years, lookfor="SegChange")

    # Arbitrarily use the first file in the file list to obtain the tile name.  This assumes that all files in the
    # directory are associated with the same H-V tile.
    # tile = get_tile(seg_files[0])
    tile = "Puget"

    # Get list of the primary cover files
    cover_files = get_files(path=indir, years=years, lookfor="CoverPrim")

    # Name the cover data pickle
    p_cover = f"{outdir}{os.sep}{tile}_cover_data.pickle"

    if not os.path.exists(p_cover):
        # Read in the Cover Data if it wasn't already pickled
        cover_data = {os.path.basename(f): read_data(f)[MASK == 1] for f in cover_files}

        # Pickle the data structure
        with open(p_cover, "wb") as p:
            pickle.dump(cover_data, p)

    # This block of code was previously used to over-write any pre-existing pickles
    # elif os.path.exists(p_cover):
    #     os.remove(p_cover)
    #
    #     # Read in the Cover Data
    #     cover_data = {os.path.basename(f): read_data(f) for f in cover_files}
    #
    #     # Pickle the data structure
    #     with open(p_cover, "wb") as p:
    #         pickle.dump(cover_data, p)

    else:
        # If the data structure was previously built, save time by reading it in rather than recreating it
        with open(p_cover, "rb") as p:
            cover_data = pickle.load(p)

    # Name the segment change pickle
    p_seg = f"{outdir}{os.sep}{tile}_segchange_data.pickle"

    if not os.path.exists(p_seg):
        # Read in the Segment Change data if the data structure wasn't previously built
        seg_data = {os.path.basename(f): read_data(f)[MASK == 1] for f in seg_files}

        # Pickle the data structure
        with open(p_seg, "wb") as p:
            pickle.dump(seg_data, p)

    else:
        # If the data structure was previously built, save time by reading it in rather than recreating it
        with open(p_seg, "rb") as p:
            seg_data = pickle.load(p)

    # Name the segment change confusion matrix pickle
    p_cnf = f"{outdir}{os.sep}{tile}_segchange_cnf.pickle"

    if not os.path.exists(p_cnf):
        # Calculate the Segment Change confusion matrices
        seg_confusion = {f: compute_confusion_matrix(seg_data[f], f) for f in seg_data.keys()}

        # Pickle the data structure
        with open(p_cnf, "wb") as p:
            pickle.dump(seg_confusion, p)

    else:
        # If the data structure was previously built, save time by reading it in rather than recreating it
        with open(p_cnf, "rb") as p:
            seg_confusion = pickle.load(p)

    # Get the Originating Class values
    seg_from = {f: seg_confusion[f][1:, -1:].flatten() for f in seg_confusion.keys()}

    # Get the Destination Class values
    seg_to = {f: seg_confusion[f][-1:, 1:].flatten() for f in seg_confusion.keys()}

    # Create DataFrame
    seg_from_df = pd.DataFrame(seg_from, index=[0, 1, 2, 3, 4, 5, 6, 7, 8, "Total"], columns=seg_from.keys())

    # Create DataFrame
    seg_to_df = pd.DataFrame(seg_to, index=[0, 1, 2, 3, 4, 5, 6, 7, 8, "Total"], columns=seg_to.keys())

    # Make Column names = years
    seg_from_df.columns = [k.split("_")[1] for k in seg_from.keys()]

    # Make Column names = years
    seg_to_df.columns = [k.split("_")[1] for k in seg_to.keys()]

    # Get the Origin Class percentages
    seg_from_df_perc = seg_from_df.iloc[seg_from_df.index != "Total"].div(seg_from_df.iloc[seg_from_df.index
                                                                                           != "Total"].sum(0) / 100, 1)

    # Get the Destination Class percentages
    seg_to_df_perc = seg_to_df.iloc[seg_to_df.index != "Total"].div(seg_to_df.iloc[seg_to_df.index !=
                                                                                   "Total"].sum(0) / 100, 1)

    # Create a dict of the class quantities that had segment change
    seg_class_totals = {key: list(seg_confusion[key][:, -1][1:-1]) for key in seg_confusion.keys()}

    # Name the class totals pickle
    p_class_totals = f"{outdir}{os.sep}{tile}_class_totals.pickle"

    if not os.path.exists(p_class_totals):
        # Create a dict of the overall class quantities
        class_totals = {key: [np.bincount(cover_data[key].flatten())[c] for c in classes] for key in cover_data.keys()}

        # Pickle the data structure
        with open(p_class_totals, "wb") as p:
            pickle.dump(class_totals, p)


    # elif os.path.exists(p_class_totals):
    #     os.remove(p_class_totals)
    #
    #     # Create a dict of the overall class quantities
    #     class_totals = {key: [np.bincount(cover_data[key].flatten())[c] for c in classes] for key in cover_data.keys()}
    #
    #     # Pickle the data structure
    #     with open(p_class_totals, "wb") as p:
    #         pickle.dump(class_totals, p)

    else:
        with open(p_class_totals, "rb") as p:
            class_totals = pickle.load(p)

    # Create an XlsxWriter object to create a workbook with multiple sheets
    xlsx_name = outdir + os.sep + tile + "_segment_analysis.xlsx"

    writer = pd.ExcelWriter(xlsx_name, engine="xlsxwriter")

    workbook = writer.book

    worksheet = workbook.add_worksheet("Summary")

    writer.sheets["Summary"] = worksheet

    seg_from_df.to_excel(writer, sheet_name="Summary", startrow=1, startcol=1)

    seg_to_df.to_excel(writer, sheet_name="Summary", startrow=14, startcol=1)

    seg_from_df_perc.to_excel(writer, sheet_name="Summary", startrow=27, startcol=1)

    seg_to_df_perc.to_excel(writer, sheet_name="Summary", startrow=39, startcol=1)

    format = workbook.add_format({"bold": True})

    worksheet.write("C1", "Segment Change Originating Class Count", format)

    worksheet.write("C14", "Segment Change Destination Class Count", format)

    worksheet.write("C27", "Segment Change Originating Class Percent", format)

    worksheet.write("C39", "Segment Change Destination Class Percent", format)

    for ind, f in enumerate(seg_files):
        # Make a key for the segment change dictionary
        segkey = os.path.basename(f)

        # Make a key for the cover map dictionary
        coverkey = os.path.basename(cover_files[ind])

        # Get the filename and current year based on the current segment change file
        fname, current_year = get_fname(f)

        # Create an output filename for the .png
        img_name = outdir + os.sep + fname + "_fig.png"

        print(f"\nWorking on file: {segkey}")

        # Write the segment change confusion matrix to a temporary .csv file
        write_to_csv(seg_confusion[segkey], outdir, fname)

        # Make a DataFrame from the segment change confusion matrix
        seg_df = array_to_dataframe(seg_confusion[segkey])

        # Get DataFrame for the quantity of cover and percentage of cover classes
        cover_table, cover_perc_table = get_cover_table(indata=cover_data[coverkey])

        # Make the annual segment change plots
        seg_class_areas, cover_areas, cover_percents, seg_total = get_seg_change_plots(seg_matrix=seg_confusion[segkey],
                                                                                       seg_table=seg_df,
                                                                                       cover_matrix=np.bincount(
                                                                                           cover_data[
                                                                                               coverkey].flatten()),
                                                                                       tile=tile, year=current_year,
                                                                                       out_img=img_name)

        seg_total_area = round(seg_total * 0.0009, 2)

        seg_perc = [round(seg_class_area / seg_total_area * 100, 2) for seg_class_area in seg_class_areas]

        seg_class_summary = [seg_class_areas, cover_areas[:-1], cover_percents, seg_perc]

        seg_class_summary_df = pd.DataFrame(seg_class_summary).T

        seg_class_summary_df.columns = ["Seg Area", "Total Area", "% Class", "% Breaks"]

        # Write the segment change confusion matrix, cover quantity, and cover percentages to the excel file
        # using the previously created xlsx writer object
        write_to_excel(writer=writer, df_seg=seg_df, df_cover=cover_table, df_cover_perc=cover_perc_table,
                       df_summary=seg_class_summary_df, year=current_year)

    # Close and save the excel workbook
    writer.save()

    # Generate the summary of segment change plots
    get_summary_plot(froms=[seg_from_df.iloc[:-1, seg_from_df.columns != '2015'],
                            seg_from_df_perc.iloc[:, seg_from_df_perc.columns != '2015']],
                     tos=[seg_to_df.iloc[:-1, seg_to_df.columns != '2015'],
                          seg_to_df_perc.iloc[:, seg_to_df_perc.columns != '2015']], tile=tile,
                     out_img=outdir + os.sep + tile + "_summary.png")

    get_annual_class_plot(sum_class=class_totals, sum_class_seg=seg_class_totals, tile=tile,
                          out_img=outdir + os.sep + tile + "_class_totals.png")

    # Clean up the output directory by removing the .csv files
    for root, folders, files in os.walk(outdir):
        for f in files:
            if f[-4:] == ".csv":
                os.remove(os.path.join(root, f))

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--indir', dest="indir", type=str, required=True,
                        help='Full path to the directory containing all Land Cover products')

    parser.add_argument('-o', '--output', dest="outdir", type=str, required=True,
                        help='Full path to the output folder')

    parser.add_argument('-y', '--years', type=str, required=False, nargs="*", default=None,
                        help='Optionally specify a from-to year or years.  Otherwise process all available years')

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
