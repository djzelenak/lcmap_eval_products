# -*- coding: utf-8 -*-
"""
Created on Mon Nov 20 15:05:08 2017

@author: dzelenak
"""

import os
import argparse
import subprocess


def main(rootdir, outdir, tile=None, years=None):
    
    input_list = []
    
    # Get a list of all the tile subfolders in the root input directory
    for root, folders, files in os.walk(rootdir):
        if tile is None:
            for folder in folders:
                if folder[0] == "h" or folder[0] == "H":
                    input_list.append(os.path.join(root, folder))
                
        else:
            # Otherwise, if a tile was specified only return a list containing that particular tile subfolder
            for folder in folders:
                if tile in folder:
                    input_list.append(os.path.join(root, folder))
                    
    for f in input_list:
        # Create the output subfolder within the output root directory
        outfolder = outdir + os.sep + os.path.basename(f)
        
        if not os.path.exists(outfolder):
            os.makedirs(outfolder)
        
        # Run with the years argument if it was passed any values
        if years is not None:
            subprocess.call(f"python segment_change_analysis.py -i {f}{os.sep}maps -o {outfolder} -y {years}",
                            shell=True)

        # Otherwise, run for all available years in the time series
        else:
            subprocess.call(f"python segment_change_analysis.py -i {f}{os.sep}maps -o {outfolder}", shell=True)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-i", dest="rootdir", type=str, required=True,
                        help="The full path to the root directory")
    
    parser.add_argument("-o" ,dest="outdir", type=str, required=True,
                        help="The full path to the output root directory")
    
    parser.add_argument("-t", dest="tile", type=str, required=False,
                        help="Optionally specify a tile to process")
    
    parser.add_argument("-y", dest="years", type=str, required=False, default=None, nargs="*",
                        help="Optionally specify one or more years to process")
    
    args = parser.parse_args()

    main(**vars(args))
    