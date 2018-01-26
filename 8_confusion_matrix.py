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
import string
import re
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

    target_file = None

    # # All files in path containing year string
    # templist = [item for item in filelist if year in os.path.basename(item)]

    for f in filelist:

        if re.search(r'\d+', os.path.basename(f)).group() == year:

            target_file = f

            break

    if target_file is not None:

        return target_file

    else:

        print("\nCould not locate a file for year {} in the given path {}\n".format(year, path))

        sys.exit(1)


def read_data(refdir, preddir, y, mask=None):
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

    preddata_m = np.zeros_like(preddata)

    preddata_m[refdata != 0] = preddata[refdata != 0]

    # Obtain unique class values from the reference data array
    ref = np.unique(refdata)

    ref_ = list(ref.flatten().tolist())

    ccdc = np.unique(preddata)

    ccdc_ = list(ccdc.flatten().tolist())

    # combine both classes lists and remove duplicates
    classes = ref_ + list(set(ccdc_) - set(ref_))

    classes.sort()

    ref, ccdc = None, None

    if mask is None:

        return refdata, preddata_m, classes, reffile, predfile

    else:
        mask_data = gdal.Open(mask, gdal.GA_ReadOnly).ReadAsArray()

        try:
            return refdata[mask_data == 1], preddata_m[mask_data == 1], classes, reffile, predfile

        except IndexError:
            print("The mask is not compatible with the size of the input data")
            sys.exit(1)


def compute_confusion_matrix(reference, classified, classes):
    """
    Generate a confusion matrix that shows the classification accuracy.
    Columns = Reference Data
    Rows = Classification Results
    :param reference:
    :param classified:
    :param classes:
    :return:
    """
    total = float(len(classes) ** 2)

    # create boolean arrays of all zeros
    TP = np.zeros(reference.shape, np.bool)

    FP = np.zeros(reference.shape, np.bool)

    FN = np.zeros(reference.shape, np.bool)

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

                np.logical_and(reference == r, classified == c, TP)

                confusion_matrix[classes.index(c), classes.index(r)] = np.sum(TP)

            elif classes.index(r) > classes.index(c):

                # print('column: ', c, '\trow: ', r)

                np.logical_and(reference == r, classified == c, FP)

                confusion_matrix[classes.index(c), classes.index(r)] = np.sum(FP)

            elif classes.index(r) < classes.index(c):

                # print('column: ', c, '\trow: ', r)

                np.logical_and(reference == r, classified == c, FN)

                confusion_matrix[classes.index(c), classes.index(r)] = np.sum(FN)

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

    # df = pd.DataFrame(matrix[1:, 1:], index=matrix[1:, 0], columns=matrix[0, 1:])

    ccdc_to_name = {0: "Insufficient Data", 1: "Developed", 2: "Agriculture", 3: "Grassland", 4: "Tree Cover",
                    5: "Water", 6: "Wetland", 7: "Ice/Snow", 8: "Barren", 9: "No Model-Fit", 99999999: "Total"}

    ref_to_name = ccdc_to_name.copy()
    ref_to_name[0] = "No Data"
    ref_to_name[9] = "Disturbed"
    ref_to_name[81] = "Pasture/Hay"

    # Find and replace 99999999 with "Total"
    try:

        # Find in dataframe index
        ind_list = df.index.tolist()

        for ind, item in enumerate(ind_list):

            try:
                ind_list[ind] = ccdc_to_name[item]
            except KeyError:
                continue

        df.index = ind_list

        # Find in dataframe columns
        col_list = df.columns.tolist()

        for ind, item in enumerate(col_list):

            try:
                col_list[ind] = ref_to_name[item]
            except KeyError:
                continue

        df.columns = col_list

    except ValueError:
        pass

    return df


def write_to_excel(loc, df, basename, y, startrow=3, startcol=2):
    """

    :param loc:
    :param df:
    :param basename:
    :param y:
    :return:
    """
    # Create a Pandas Excel writer using XlsxWriter as the engine
    writer = pd.ExcelWriter(loc + os.sep + "{name}.xlsx".format(name=basename),
                            engine="xlsxwriter")

    workbook = writer.book

    worksheet = workbook.add_worksheet(y)

    writer.sheets[y] = worksheet

    format_title = workbook.add_format({"bold": True, "font_size": 16})
    format_subtitle = workbook.add_format({"bold": True, "font_size": 12})
    format_labels = workbook.add_format({"bold": True, "text_wrap": True, "valign": "top", "font_size": 8})
    format_diag = workbook.add_format({"bold": True, "bg_color": "#C0C0C0", "border_color": "#000000"})

    # Convert the dataframe to an XLsxWriter Excel object
    df.to_excel(writer, sheet_name="{year}".format(year=y),
                header=False, index=False,
                startrow=startrow, startcol=startcol)

    # Use the output excel filename to construct the title displayed on the worksheet
    name_pieces = basename.split("_")

    title = ""
    subtitle = name_pieces[0].upper()

    for piece in name_pieces:
        if not "cnf" in piece:
            title = title + piece.upper() + " "

    worksheet.write(0, 1, title, format_title)

    for col_num, name in enumerate(df.columns.values):
        worksheet.write(2, col_num + 2, name, format_labels)

    for row_num, name in enumerate(df.index):
        worksheet.write(row_num + 3, 1, name, format_labels)

    worksheet.write(6, 0, "CCDC", format_subtitle)

    worksheet.write(7, 0, "Classes", format_subtitle)

    worksheet.write(1, 6, "{} Classes".format(subtitle), format_subtitle)

    # Construct a data structure for looking up the dataframe location and value
    # where reference name equals classified name
    diag_lookup = dict()

    for r, row in enumerate(df.iterrows()):

        for c, col in enumerate(df.iteritems()):

            if row[0] == col[0]:

                diag_lookup[row[0]] = {"rowcol": (r, c), "value": df.loc[row[0], col[0]]}

    def df_to_cell(rowcol, startrow, startcol):
        """
        Convert a dataframe (row, col) tuple to an excel cell identifier
        :param rowcol:
        :param startrow:
        :param startcol:
        :return:
        """
        letters = list(string.ascii_uppercase)

        numbers = [n for n in range(1, len(letters) + 1)]

        row = rowcol[0]
        col = rowcol[1]

        row_ = row + startrow
        col_ = col + startcol

        try:
            cell = str(letters[col_] + str(numbers[row_]))
            return cell
        except IndexError:
            raise

    for key in diag_lookup.keys():

        cell = df_to_cell(diag_lookup[key]["rowcol"], startrow, startcol)

        worksheet.write(cell, diag_lookup[key]["value"], format_diag)

    # Close the Pandas Excel writer and output the Excel file
    writer.save()

    return None


def main_work(ref, pred, output, year, mask=None):
    """

    :param ref:
    :param pred:
    :param output:
    :param year:
    :param mask:
    :return:
    """
    if not os.path.exists(output):
        os.makedirs(output)

    refData, predData, Classes, ref_file, pred_file = read_data(ref, pred, year, mask)

    cnf_mat = compute_confusion_matrix(refData, predData, Classes)

    fname = get_fname(ref_file, year)

    write_to_csv(cnf_mat, output, fname)

    df = array_to_dataframe(cnf_mat)

    write_to_excel(output, df, fname, year)

    print("\nAll done")

    return None


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '-ref', '--reference', dest='ref', type=str, required=True,
                        help='Full path to the reference file parent directory (Trends or NLCD)')

    parser.add_argument('-p', '-pred', '--prediction', dest='pred', type=str, required=True,
                        help='Full path to the prediction file parent directory (CCDC CoverPrim)')

    parser.add_argument('-o', '--output', dest='output', type=str, required=True,
                        help='Full path to the output folder')

    parser.add_argument('-y', '--year', dest='year', type=str, required=True,
                        help='The year used to identify matching layers for comparing in the matrix')

    parser.add_argument('-m', '--mask', dest='mask', type=str, required=False,
                        help='Optionally specify a processing mask raster')

    args = parser.parse_args()

    main_work(**vars(args))



    return None


if __name__ == '__main__':
    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S\n"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
