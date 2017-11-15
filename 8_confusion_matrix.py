# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose: Generate confusion matrix comparing pyccd and trends/nlcd land cover agreement

Horizontal Axis = Pyccd classes
Vertical Axis = Trends/NLCD classes

Last Updated: 8/4/2017, 9/7/2017
"""

import datetime
import os
import sys
import argparse
import glob
import pprint

import numpy as np

import pandas as pd

from osgeo import gdal

gdal.UseExceptions()
gdal.AllRegister()

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S\n"))


def get_file(path, year):
    """

    :param path: <str>
    :param year: <str>
    :return:
    """

    # All files in path ending in .tif
    filelist = glob.glob("{p}{sep}*.tif".format(p=path, sep=os.sep))

    filelist.sort()

    # All files in path containing year string
    templist = [item for item in filelist if year in os.path.basename(item)]

    if len(templist) == 0:
        print("\nCould not locate a file for year {} in the given path {}\n".format(year, path))

        print("Available files in path are:\n")

        pprint.pprint(filelist)

        sys.exit(1)

    elif len(templist) == 1:
        return templist[0]

    else:
        # Because NLCD files have 2 years in their filenames

        return templist[-1]


def read_data(refdir, preddir, y):
    """

    :param refdir: <str> Full path to the directory containing the reference land cover
    :param preddir: <str> Full path to the directory containing the predicted land cover
    :param y: <str> The target year
    :return:
    """
    reffile = get_file(refdir, y)

    predfile = get_file(preddir, y)

    print("The reference file is:\n\t{}\n".format(reffile))

    print("The prediction file is:\n\t{}\n".format(predfile))

    # Load raster data into arrays
    refdata = gdal.Open(reffile, gdal.GA_ReadOnly).ReadAsArray()

    preddata = gdal.Open(predfile, gdal.GA_ReadOnly).ReadAsArray()

    # Obtain unique class values from the reference data array
    ref = np.unique(refdata)

    ref_ = list(ref.flatten().tolist())

    ccdc = np.unique(preddata)

    ccdc_ = list(ccdc.flatten().tolist())

    # combine both classes lists and remove duplicates
    classes = ref_ + list(set(ccdc_) - set(ref_))

    classes.sort()

    ref, ccdc = None, None

    return refdata, preddata, classes, reffile, predfile


def compute_confusion_matrix(truth, predicted, classes):
    total = float(len(classes) ** 2)

    # create boolean arrays of all zeros
    TP = np.zeros(truth.shape, np.bool)

    FP = np.zeros(truth.shape, np.bool)

    FN = np.zeros(truth.shape, np.bool)

    # create the confusion matrix, for now containing all zeros
    confusion_matrix = np.zeros((len(classes), len(classes)), np.int32)

    print("generating %s by %s confusion matrix" % (len(classes), len(classes)))

    counter = 1.0
    # loop through columns
    for c in classes:
        # loop through rows
        for r in classes:

            current = counter / total * 100.0  # as percent

            if c == r:  # TP case

                # print('column: ', c, '\trow: ', r)

                np.logical_and(truth == r, predicted == c, TP)

                confusion_matrix[classes.index(r), classes.index(c)] = np.sum(TP)

            elif classes.index(r) > classes.index(c):

                # print('column: ', c, '\trow: ', r)

                np.logical_and(truth == r, predicted == c, FP)

                confusion_matrix[classes.index(r), classes.index(c)] = np.sum(FP)

            elif classes.index(r) < classes.index(c):

                # print('column: ', c, '\trow: ', r)

                np.logical_and(truth == r, predicted == c, FN)

                confusion_matrix[classes.index(r), classes.index(c)] = np.sum(FN)

            # show the percent complete
            sys.stdout.write("\r%s%% Done " % str(current)[:5])

            # needed to display the current percent complete
            sys.stdout.flush()

            counter += 1.0

        sys.stdout.flush()

    # add row totals in a new column at the end
    x_sum = confusion_matrix.sum(axis=1)

    x_sum = np.reshape(x_sum, (len(classes), 1))

    confusion_matrix = np.append(arr=confusion_matrix, values=x_sum, axis=1)

    # add column totals in a new row at the end
    y_sum = confusion_matrix.sum(axis=0)

    y_sum = np.reshape(y_sum, (1, len(classes) + 1))

    confusion_matrix = np.append(arr=confusion_matrix, values=y_sum, axis=0)

    # insert a blank row and column at the top/left to contain class values
    confusion_matrix = np.insert(arr=confusion_matrix, obj=0, axis=0, values=0)

    confusion_matrix = np.insert(arr=confusion_matrix, obj=0, axis=1, values=0)

    # so len(classes) matches row/column shape of confusion matrix
    classes.insert(0, 0)

    # 99999999 instead of 'total' because can't have strings in array of numbers
    classes.append(99999999)

    # insert the class names into the blank columns/rows of the matrix
    for c in range(len(classes)):
        confusion_matrix[c, 0] = classes[c]

        confusion_matrix[0, c] = classes[c]

    return confusion_matrix


def get_fname(ref, y):
    names = ["nlcd", "NLCD", "trends", "Trendsblock", "Trends", "QA", "CoverPrim", "CoverSec"]

    name = None

    for n in names:

        if n in os.path.basename(ref):

            name = n

            if name == "Trendsblock" or name == "Trends":
                name = "trends"

            break

    # Create a name for the confusion matrix .csv file
    f_name = "{name}_pyccdc_{year}_cnfmatrix".format(name=name, year=y)

    return f_name


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
    # Create a copy of the original numpy array to preserve it
    holder = np.copy(matrix)

    # Remove empty rows
    cnf_mat1 = np.copy(holder)

    for row in range(np.shape(matrix)[0] - 1, -1, -1):
        try:
            test_row = matrix[row, 1:]

            if np.all(test_row == 0):
                cnf_mat_ = np.delete(cnf_mat1, row, axis=0)

                cnf_mat1 = np.copy(cnf_mat_)

        except IndexError:
            pass

    # Remove empty columns
    cnf_mat2 = np.copy(cnf_mat1)

    for c in range(np.shape(cnf_mat1)[1] - 1, -1, -1):
        try:
            test_col = cnf_mat1[1:, c]

            if np.all(test_col == 0):
                cnf_mat_ = np.delete(cnf_mat2, c, axis=1)

                cnf_mat2 = np.copy(cnf_mat_)

        except IndexError:
            pass

    # Dataframe with empty rows and columns removed
    df = pd.DataFrame(cnf_mat2[1:, 1:], index=cnf_mat2[1:, 0], columns=cnf_mat2[0, 1:])

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


def write_to_excel(loc, df, basename, y):
    # Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(loc + os.sep + "{name}.xlsx".format(name=basename),
                            engine="xlsxwriter")

    # Convert the dataframe to an XLsxWriter Excel object
    df.to_excel(writer, sheet_name="{year}".format(year=y))

    # Close the Pandas Excel writer and output the Excel file
    writer.save()

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '-ref', '--reference', type=str, required=True,
                        help='Full path to the reference file parent directory (Trends or NLCD)')

    parser.add_argument('-p', '-pred', '--prediction', type=str, required=True,
                        help='Full path to the prediction file parent directory (CCDC CoverPrim)')

    parser.add_argument('-o', '--output', type=str, required=True,
                        help='Full path to the output folder')

    parser.add_argument('-y', '--year', type=str, required=True,
                        help='The year used to identify matching layers for comparing in the matrix')

    args = parser.parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    refData, predData, Classes, ref_file, pred_file = read_data(args.reference, args.prediction, args.year)

    cnf_mat = compute_confusion_matrix(refData, predData, Classes)

    fname = get_fname(ref_file, args.year)

    write_to_csv(cnf_mat, args.output, fname)

    df = array_to_dataframe(cnf_mat)

    write_to_excel(args.output, df, fname, args.year)

    pprint.pprint(df)

    print("\nAll done")

    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
