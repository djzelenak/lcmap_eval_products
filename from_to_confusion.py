# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose: Generate confusion matrix comparing pyccd and trends/nlcd land cover agreement

Horizontal Axis = To classes
Vertical Axis = From classes

"""

import argparse
import datetime
import glob
import os
import sys
import traceback
import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
from osgeo import gdal

gdal.UseExceptions()
gdal.AllRegister()

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S\n"))


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


def get_files(path, years=None, lookfor="SegChange"):
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
    filelist = glob.glob(f"{path}{os.sep}*{lookfor}*.tif")

    filelist.sort()

    if len(filelist) == 0:
        print("\nCould not locate a files {}\n".format(path))

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

    return basename, basename[-4:]


def compute_confusion_matrix(fromto):
    """
    Calculate the confusion matrix for the current from-to data set
    :param fromto: An array object containing the from-to data
    :type fromto: numpy.ndarray
    :return:
    """
    from_vals = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    to_vals = [0, 1, 2, 3, 4, 5, 6, 7, 8]

    total = float(len(from_vals) * len(to_vals))

    check_vals = np.unique(fromto)

    # Temporary gross fix
    for ind, v in enumerate(check_vals):
        if len(str(v)) == 1:
            check_vals[ind] = v * 10


    # create the confusion matrix, for now containing all zeros
    confusion_matrix = np.zeros((len(from_vals), len(to_vals)), np.int32)

    print("generating %s by %s confusion matrix" % (len(to_vals), len(from_vals)))

    counter = 1.0

    # loop through columns
    for c in to_vals:

        # loop through rows
        for r in from_vals:
            val = int(str(c) + str(r))
            current = counter / total * 100.0  # as percent

            if val in check_vals and val != 0:
                # (c, r) means 'from' is vertical axis and 'to' is the horizontal axis

                if str(val)[1] != "0":
                    confusion_matrix[to_vals.index(c), from_vals.index(r)] = np.bincount(fromto.flatten())[val]

                else:
                    confusion_matrix[to_vals.index(c), from_vals.index(r)] = np.bincount(fromto.flatten())[int(str(val)[0])]

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


def write_to_excel(writer, df, year):

    # Convert the dataframe to an XLsxWriter Excel object
    df.to_excel(writer, sheet_name=year, startrow=1, startcol=1)

    workbook = writer.book

    worksheet = writer.sheets[year]

    format = workbook.add_format({"bold": True})
    format2 = workbook.add_format({"bold": True, "bg_color": "#C0C0C0" })

    worksheet.write(0, 6, "Destination", format)
    worksheet.write(6, 0, "Origin", format)

    # TODO Change background color of diagonal cells
    # worksheet.write("C3, D4, E5, F6, G7, H8, I9, J10, K11, L12", format2)

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

    return percents.div(percents.sum(1)/100, 0)


def get_class_totals(matrix):
    """
    First slice the matrix to get all rows of the last column.  Then, remove the first row from this slice because
    it is just a column header value.  Also, don't include the last element because this is the overall total
    :param matrix: The from-to counts array
    :return: The column from the from-to array containing class totals
    :rtype: numpy.ndarray
    """
    return matrix[:,-1][1:-1]


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

    return total_count / 25000000.0 * 100.0


def get_plot(matrix, table, tile, year, out_img):
    """

    :param matrix: <numpy.ndarray>
    :param table: <pandas.core.frame.DataFrame>
    :return: None
    """
    def autolabel(rects, ax, totals):
        """
        Generate labels for the horizontal bar plot.  Use the class totals as the label values
        :param rects:
        :param ax:
        :return:
        """

        for ind, rect in enumerate(rects):
            width = int(rect.get_width())

            if width < 20:
                xloc = width + 5
                clr="k"
                align = "right"
            else:
                xloc=0.98 * width
                clr="k"
                align="left"

            yloc = rect.get_y() + rect.get_height()/2.0

            label = ax.text(xloc, yloc, "{:02.2f} $km^2$".format(totals[ind]), ha=align, va="center",
                            color=clr, weight="bold", clip_on=True, fontsize=10)

        return None


    df_class_percents = get_fromclass_percents(table)

    class_totals = (get_class_totals(matrix)).astype(np.int64)

    class_areas = [round(class_total * 900 * .0009, 2) for class_total in class_totals]

    segments_total = get_segments_total(matrix)

    class_segment_proportions = [class_total / segments_total * 100.0 for class_total in class_totals]

    total_thematic_percent = get_thematic_change_percent(matrix)

    total_segment_percent = segments_total / 25000000.0 * 100.0

    matplotlib.style.use("ggplot")

    colors = [(0.0, 0.0, 0.0),
              (1.0, 0.0, 0.0),
              (1.0, 0.6470588235294118, 0.0),
              (1.0, 1.0, 0.0),
              (0.0, 0.5490196078431373, 0.0),
              (0.0, 0.0, 1.0),
              (0.0, 1.0, 1.0),
              (0.9, 0.9, 0.9),
              (0.39215686274509803, 0.39215686274509803, 0.39215686274509803)]

    # Create the figure with two subplots that share a y-axis
    fig, (ax1, ax2) = plt.subplots(figsize=(15, 5), dpi=200, nrows=1, ncols=2, sharex=False, sharey=True)

    # Use the DataFrame class_percents to plot the proportion of change in each originating class on the right axis
    df_class_percents[:-1].plot.barh(stacked=True, color=colors, ax=ax2, edgecolor="k", width=0.5, legend=False)

    # Use array class_segment_proportions to plot the proportion of each class to the segments total
    rects = ax1.barh(np.arange(len(class_segment_proportions)), class_segment_proportions,
                     color=colors, height=0.5, edgecolor="k")

    # Add class total labels to the horizontal bars
    autolabel(rects=rects, ax=ax1, totals=class_areas)

    # Plot the first class at the top, this inverts the y-axis for both subplots because they share y
    ax1.invert_yaxis()

    # Invert the x-axis on the left subplot so that it matches the origin of the right subplot
    ax1.invert_xaxis()

    # Add figure title and subtitles
    fig.suptitle(f"{tile} {year}", fontsize=18, y=1.10)
    plt.figtext(0.5, 0.99, f"Segment Change in {round(total_segment_percent, 2)}% of Tile", fontsize=12, ha="center")
    plt.figtext(0.5, 0.93, f"Cover Change in {round(total_thematic_percent, 2)}% of Tile", fontsize=12, ha="center")

    # Add subplot titles
    ax1.set_title("Percent of Origin Class in All Segment Changes", fontsize=12)
    ax2.set_title("Percent of Class Destination from Origin Class", fontsize=12)

    # Add axes labels and titles
    ax1.set_xlabel("Percent", fontsize=12)
    ax2.set_xlabel("Percent", fontsize=12)
    ax1.set_yticklabels([""]*len(np.arange(9)))
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
    ax1.legend(handles=handles, loc="upper right", bbox_to_anchor=(0, 0.99), ncol=1, labelspacing=1.94,
               markerfirst=False, facecolor="w", frameon=False)

    # Adjust subplots to make enough room at the top for figure titles
    fig.subplots_adjust(top=0.85)

    # Adjust subplots so that there is no space between the y-axes
    fig.subplots_adjust(wspace=0)

    plt.savefig(out_img, dpi=200, bbox_inches="tight")

    plt.close()

    return None


def main_work(indir, outdir, years=None):
    """

    :param indir:
    :param outdir:
    :param year:
    :return:
    """
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    files = get_files(path=indir, years=years)

    # Arbitrarily use the first file in the file list to obtain the tile name.  This assumes that all files in the
    # directory are associated with the same H-V tile.
    tile = get_tile(files[0])

    # Create an XlsxWriter object to create a workbook with multiple sheets, make sure not to overwrite an existing
    # workbook by checking os.path.exists(xlsx_name)
    xlsx_name = outdir + os.sep + tile + "_cnfmat.xlsx"

    if not os.path.exists(xlsx_name):
        writer = pd.ExcelWriter(xlsx_name, engine="xlsxwriter")

    else:
        xlsx_name = os.path.splitext(xlsx_name)[0]

        xlsx_name = xlsx_name + "_1.xlsx"

        writer = pd.ExcelWriter(xlsx_name, engine="xlsxwriter")

    for f in files:
        fname, current_year = get_fname(f)

        img_name = outdir + os.sep + fname + "_fig.png"

        # Skip file "f" if the excel file associated with f exists
        if os.path.exists(img_name):
            continue

        print(f"\nWorking on file: {f}")

        in_data = read_data(f)

        try:
            cnf_mat = compute_confusion_matrix(fromto=in_data)

        except IndexError:
            error_message(f)

            continue

        write_to_csv(cnf_mat, outdir, fname)

        df = array_to_dataframe(cnf_mat)

        write_to_excel(writer=writer, df=df, year=current_year)

        get_plot(matrix=cnf_mat, table=df, tile=tile, year=current_year, out_img=img_name)

    writer.save()

    # Clean up the output directory by removing the .csv files
    for root, folders, files in os.walk(outdir):
        for f in files:
            if f[-4:] == ".csv":
                os.remove(os.path.join(root, f))

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--indir', dest="indir", type=str, required=True,
                        help='Full path to the directory containing From-To layers')

    parser.add_argument('-o', '--output', dest="outdir", type=str, required=True,
                        help='Full path to the output folder')

    parser.add_argument('-y', '--years', type=str, required=False, nargs="*", default=None,
                        help='Optionally specify a from-to year.  Otherwise process all available years')

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
