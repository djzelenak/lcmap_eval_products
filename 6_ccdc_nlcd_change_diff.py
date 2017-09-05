"""
Author: Dan Zelenak
Date:	8/5/2015 (by Dev Dahal)
Last Updated: 2/2/2017 by Dan Zelenak to work on LCSRLNST01
and 2/6/2017 to compute CCDC vs nlcd change difference (output int16)
9/5/2017 to be compatible with python 3.6

Purpose:
Compare the number of NLCD LC changes and PyCCD spectral changes between two years
"""

import datetime
import glob
import os
import subprocess
import sys
import traceback

print (sys.version)

t1 = datetime.datetime.now()

print(t1.strftime("%Y-%m-%d %H:%M:%S"))


Layers2Years = {}

for i, j in zip(range(1, 31), range(1985, 2015)):

    Layers2Years.update({j: i})


def allCalc(inNLCD, inCCDC, outDir, FromY, ToY):

    try:

        if not os.path.exists(outDir):

            os.makedirs(outDir)

        inCCDCList = glob.glob(inCCDC + os.sep + "*.tif")
        inNLCDList = glob.glob(inNLCD + os.sep + "*.tif")

        inCCDCList.sort()
        inNLCDList.sort()

        frmY, toY = FromY[-2:], ToY[-2:]  # take the last two digits from the years for file naming

        file1 = '%s/nlcd%sto%sct.tif' % (inNLCD, frmY, toY)
        file2 = '%s/ccdc%sto%sct.tif' % (inCCDC, FromY, ToY)

        if not os.path.exists(file1):

            print('layer %s does not exist for this tile'.format(os.path.basename(file1)))

            return None

        print("\n\tmatched layers are: \n", file1, "\n", file2, "\n")
          # for testing

        print('\nFiles are saving in', outDir)
          # for testing

        FileF = 'GTiff'

        bandFile = '%s/nlcd%sto%sct_ccdc%sto%sct.tif' % (outDir, frmY, toY, frmY, toY)

        tempYear = outDir + os.sep + "zzzz_1.tif"

        tempYear1 = outDir + os.sep + "zzzz_2.tif"

        if not os.path.exists(bandFile):

            runCalc = '/usr/bin/gdal_calc.py --format %s --type %s -A %s -B %s --outfile %s --calc="(A * 100.0 + B)" ' \
                      % (FileF, 'Int16', file1, file2, bandFile)

            subprocess.call(runCalc, shell=True)  # --NoDataValue 0

        else:

            print("%s was already processed".format(os.path.basename(bandFile)))

    except:

        print(traceback.format_exc())

    return None

def usage():

    print('Usage:python 6_ccdc_nlcd_change_diff.py\n\n \
       [-ic Full path to the input CCDC change map layers]\n \
       [-ir Full path to the reference NLCD change map layers]\n\
       [-of outfile format (only 3 format supported: GTiff, HFA, and GRID)]\n \
       [-frm From Year]\n \
       [-to To Year]\n \
       [-o Main output directory]\n\n')

    return None

def main():

    fromY, toY = None, None

    argv = sys.argv

    if argv is None:

        print("try -help")

        sys.exit(1)

    # Parse command line arguments.
    i = 1
    while i < len(argv):
        arg = argv[i]

        if arg == '-ir':
            i = i + 1
            inputNLCD = argv[i]

        elif arg == '-ic':
            i = i + 1
            inputCCDC = argv[i]

        elif arg == '-frm':
            i = i + 1
            fromY = argv[i]

        elif arg == '-to':
            i = i + 1
            toY = argv[i]

        elif arg == '-o':
            i = i + 1
            outputDir = argv[i]

        elif arg == '-help':
            usage()
            sys.exit(1)

        elif arg[:1] == ':':
            print('Unrecognized command option: %s' % arg)
            usage()
            sys.exit(1)

        i += 1

    # call the primary function
    allCalc(inputNLCD, inputCCDC, outputDir, fromY, toY)

if __name__ == '__main__':

    main()

t2 = datetime.datetime.now()

print(t2.strftime("%Y-%m-%d %H:%M:%S"))

tt = t2 - t1

print("\tProcessing time: " + str(tt))
