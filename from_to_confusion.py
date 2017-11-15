# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose: Generate confusion matrix comparing pyccd and trends/nlcd land cover agreement

Horizontal Axis = Pyccd classes
Vertical Axis = Trends/NLCD classes

"""

import argparse
import datetime
import glob
import os
import sys
import traceback

import numpy as np
import pandas as pd
from osgeo import gdal

gdal.UseExceptions()
gdal.AllRegister()

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S\n"))


def get_files(path, year=None, lookfor="CoverFromTo"):
    """

    :param path:
    :param year:
    :param lookfor:
    :return:
    """
    # All files in path ending in .tif
    filelist = glob.glob(f"{path}{os.sep}{lookfor}*.tif")

    filelist.sort()

    if len(filelist) == 0:
        print("\nCould not locate a files {}\n".format(path))

        sys.exit(1)

    if year is None:
        return filelist

    else:
        return [f for f in filelist if year in f]


def read_data(infile):
    """

    :param infile:
    :return:
    """
    # Load raster data into an array
    data = gdal.Open(infile, gdal.GA_ReadOnly).ReadAsArray()

    # Obtain unique class values from the array
    vals = np.unique(data)

    return data

def get_fname(infile):
    basename = os.path.splitext(os.path.basename(infile))[0]

    return f"{basename}_cnf"


def compute_confusion_matrix(fromto, from_vals, to_vals):
    """

    :param fromto: <np.ndarray>
    :param from_vals: <list>
    :param to_vals: <list>
    :return:
    """
    total = float(len(from_vals) * len(to_vals))

    check_vals = np.unique(fromto)

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

            if val in check_vals:
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


def write_to_csv(matrix, outdir, name):
    lookfor = '99999999'

    if os.path.exists('%s/%s.csv' % (outdir, lookfor)):
        os.remove('%s/%s.csv' % (outdir, lookfor))

    if os.path.exists('%s/%s.csv' % (outdir, name)):
        os.remove('%s/%s.csv' % (outdir, name))

    # save the confusion matrix to a temporary .csv file named 999999.csv
    np.savetxt('%s/%s.csv' % (outdir, lookfor), matrix, fmt='%d')

    # open the temp .csv file and a new final output csv file named with the fname variable
    with open('%s/%s.csv' % (outdir, lookfor), 'r') as f:

        text = f.read()

        text = text.replace(lookfor, 'Total')

    with open('%s/%s.csv' % (outdir, name), 'w') as out:

        out.write(text)

    for dirpath, folders, files in os.walk(outdir):

        for x in files:

            if x == '99999999.csv':
                os.remove(os.path.join(dirpath, x))

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


def write_to_excel(loc, df, basename):
    # Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(loc + os.sep + "{name}.xlsx".format(name=basename),
                            engine="xlsxwriter")

    # Convert the dataframe to an XLsxWriter Excel object
    df.to_excel(writer, sheet_name=f"{basename}")

    # Close the Pandas Excel writer and output the Excel file
    writer.save()

    return None


def main_work(indir, outdir, year=None):
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    files = get_files(path=indir, year=year)

    for f in files:
        print(f"Working on file: {f}")

        in_data = read_data(f)

        try:
            froms, tos =[1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 3, 4, 5, 6, 7, 8]

            cnf_mat = compute_confusion_matrix(fromto=in_data, from_vals=froms, to_vals=tos)

        except IndexError:
            print(f"Skipping file {f}")
            print("Type of Exception: ", sys.exc_info()[0])
            print("Exception Value: ", sys.exc_info()[1])
            print("Traceback Info: ")
            traceback.print_tb(sys.exc_info()[2])
            continue

        fname = get_fname(f)

        write_to_csv(cnf_mat, outdir, fname)

        df = array_to_dataframe(cnf_mat)

        write_to_excel(outdir, df, fname)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--indir', dest="indir", type=str, required=True,
                        help='Full path to the directory containing From-To layers')

    parser.add_argument('-o', '--output', dest="outdir", type=str, required=True,
                        help='Full path to the output folder')

    parser.add_argument('-y', '--year', type=str, required=False,
                        help='The year used to identify matching layers for comparing in the matrix')

    args = parser.parse_args()

    main_work(**vars(args))

    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
