# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 14:05:09 2017

@author: dzelenak

Purpose:

Last Updated: 8/4/2017
"""

import datetime
import os
import sys

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import numpy as np

from osgeo import gdal

import argparse

gdal.UseExceptions()
gdal.AllRegister()

t1 = datetime.datetime.now()
print(t1.strftime("%Y-%m-%d %H:%M:%S\n"))


def readData(reffile, predfile):

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


def plot_confusion_matrix(df_confusion, title, normalize=True, cmap=plt.cm.RdYlGn):
    # define a function for generating graphical plot output of the confusion matrix

    # plt.imshow(df_confusion, interpolation='cubic', cmap=cmap
    plt.matshow(df_confusion, cmap=cmap)  # imshow

    plt.title(title)

    plt.colorbar()

    tick_marks = np.arange(len(df_confusion.columns))

    plt.xticks(tick_marks, df_confusion.columns, rotation=90)

    plt.yticks(tick_marks, df_confusion.index)

    # plt.tight_layout()

    plt.ylabel(df_confusion.index.name)

    plt.xlabel(df_confusion.columns.name)

    return None


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


def usage():

    print("\n\tUsage: Generate a confusion matrix to compare NLCD and CCD LC\n"
          "\t[-ir Full path to the reference file (Trends or NLCD)]\n"
          "\t[-ip Full path to the prediction file (CCDC)]\n"
          "\t[-plt Either Yes,Y,y, or YES to generate a plot (default is No)]\n"
          "\t[-o Main output directory]\n\n"
          "\tExample: python confusion_matrix.py -r C:/... -p C:/..."
          "\n\t-o C:/... plt N")

    return None


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '-ref', '--reference', type=str, required=True,
                        help='Full path to the reference file (Trends or NLCD)')

    parser.add_argument('-p', '-pred', '--prediction', type=str, required=True,
                        help='Full path to the prediction file (CCDC)')

    parser.add_argument('-plt', '--plot', type=bool, choice=[True, False], required=False,
                        help='Either True or False to generate a plot (default is False)')

    parser.add_argument('-o', '--output', type=str, required=True,
                        help='Full path to the output folder')

    args = parser.parse_args()

    out_dir = args.output

    ref_file = args.reference

    pred_file = args.prediction

    plot_yn = args.plot

    if not os.path.exists(out_dir):

        os.makedirs(out_dir)

    refData, predData, Classes = readData(ref_file, pred_file)

    cnf_mat = compute_confusion_matrix(refData, predData, Classes)

    print("\n", cnf_mat, "\n")

    # create a name for the confusion matrix .csv file
    fname = '{}_{}_cnfmatrix'.format(os.path.basename(ref_file)[:-4], os.path.basename(pred_file)[:-4])

    if plot_yn:

        print("\nGenerating graphical plot now...")

        # Run the plot function
        plot_confusion_matrix(cnf_mat, fname)

        plt.show()

    write_to_csv(cnf_mat, out_dir, fname)

    print("All done")

    return None


if __name__ == '__main__':

    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
