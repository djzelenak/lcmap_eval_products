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
    
    for root, folders, files in os.walk(rootdir):
        if tile is None:
            for folder in folders:
                input_list.append(os.path.join(root, folder))
                
        else:
            for folder in folders:
                if tile in folder:
                    input_list.append(os.path.join(root, folder))
                    
    for f in input_list:
        
        outfolder = outdir + os.sep + os.path.basename(f) + "_cnf"
        
        if not os.path.exists(outfolder):
            os.makedirs(outfolder)
        
        subprocess.call(f"python from_to_confusion.py -i {f} -o {outfolder} -y {years}", shell=True)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    
    parser.add_argument("-i", dest="rootdir", type=str, required=True,
                        help="The full path to the root directory")
    
    parser.add_argument("-o" ,dest="outdir", type=str, required=True,
                        help="The full path to the output root directory")
    
    parser.add_argument("-t", dest="tile", type=str, required=False,
                        help="Optionally specify a tile to process")
    
    parser.add_argument("-y", dest="years", type=str, required=False, nargs="*",
                        help="Optionally specify one or more years to process")
    
    args = parser.parse_args()

    main(**vars(args))
    