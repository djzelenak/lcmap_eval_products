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
import glob

import numpy as np

from osgeo import gdal

import argparse

gdal.UseExceptions()
gdal.AllRegister()

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S\n"))


def get_file(path, year):
    """

    :param path: Location to search for the appropriate input file based on year
    :type path: str
    :param name:
    :param year:
    :return: Item from templist based on the matching year
    """

    filelist = glob.glob("{p}{sep}*.tif".format(p=path, sep=os.sep))

    filelist.sort()

    templist = [item for item in filelist if year in os.path.basename(item)]

    if len(templist) == 0:

        print("\nCould not locate a file in the give path {}\n".format(path))

        sys.exit(0)

    elif len(templist) == 1:

        return templist[0]

    else:

        return templist[-1]


def readData(refdir, preddir, y):

    reffile = get_file(refdir, y)

    predfile = get_file(preddir, y)

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

    return refdata, preddata, classes


def compute_confusion_matrix(truth, predicted, classes):
    total = float(len(classes) ** 2)

    # create boolean arrays of all zeros
    TP = np.zeros(truth.shape, np.bool)

    FP = np.zeros(truth.shape, np.bool)

    FN = np.zeros(truth.shape, np.bool)

    # create the confusion matrix, for now containing all zeros
    confusion_matrix = np.zeros((len(classes), len(classes)), np.int32)

    print("generating %s by %s confusion matrix" % (len(classes), len(classes)))

    # iterate through the unique classes
    counter = 1.0

    for c in classes:  # iterate through columns

        for r in classes:  # iterate through rows

            current = counter / total * 100.0  # as percent

            if c == r:  # TP case

                # print 'column: ', c, '\trow: ', r

                np.logical_and(truth == r, predicted == c, TP)

                confusion_matrix[classes.index(r), classes.index(c)] = np.sum(TP)

            elif classes.index(r) > classes.index(c):

                # print 'column: ', c, '\trow: ', r

                np.logical_and(truth == r, predicted == c, FP)

                confusion_matrix[classes.index(r), classes.index(c)] = np.sum(FP)

            elif classes.index(r) < classes.index(c):

                # print 'column: ', c, '\trow: ', r

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

    parser.add_argument('-n', '--name', type=str, required=True,
                        help='File name to match for')

    args = parser.parse_args()

    out_dir = args.output

    ref_dir = args.reference

    pred_dir = args.prediction

    if not os.path.exists(args.output):

        os.makedirs(args.output)


    refData, predData, Classes = readData(args.reference, args.prediction, args.year)

    cnf_mat = compute_confusion_matrix(refData, predData, Classes)

    print("\n", cnf_mat, "\n")

    names = ['nlcd', 'trends']

    for n in names:

        if n in args.reference:

            name = n

        else:

            name = "ref"

    # create a name for the confusion matrix .csv file
    fname = '{}_{}_{}_cnfmatrix'.format(name, "ccdc", args.year)

    write_to_csv(cnf_mat, args.output, fname)

    print("All done")

    return None


if __name__ == '__main__':

    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
