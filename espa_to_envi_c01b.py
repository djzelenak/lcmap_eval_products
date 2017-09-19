import os
import subprocess
import multiprocessing as mp
import tarfile
import shutil
import logging
import sys
import argparse

from osgeo import gdal

WORK_DIR = '/lcmap_data/working/dataprep/dzelenak'
#WORK_DIR = r"C:\Working"
#%%
# GDAL_PATH = os.environ.get('GDAL')
# if not GDAL_PATH:
#     raise Exception('GDAL environment variable not set')
#
# GDAL_PATH = os.path.join(GDAL_PATH, 'bin')
#%%
LOGGER = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
handler.setFormatter(formatter)
LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

#%%
def create_tiles(inpath, outpath, worker_num):
    if not os.path.exists(outpath):
        os.makedirs(outpath)

    file_q = mp.Queue()
    message_q = mp.Queue()

    file_enqueue(inpath, file_q, worker_num)
    work = work_paths(worker_num, WORK_DIR)
    
    message = mp.Process(target=progress, args=(message_q, worker_num))
    message.start()
    for i in range(worker_num - 1):
        p_args = (file_q, message_q, outpath, work[i])
        mp.Process(target=process_tile, args=p_args).start()

    message.join()

#%%
def unpackage(file, work_path):
    with tarfile.open(file) as f:
        f.extractall(path=work_path)

#%%
def translate(pathing):
    subprocess.call('gdal_translate -of GTiff {} {}'
                    .format(pathing['TRAN']['IN'], pathing['TRAN']['OUT']), shell=True)

#%%
def vrt(pathing):
    subprocess.call('gdalbuildvrt -separate {} {}'
                    .format(pathing['VRT']['OUT'], pathing['VRT']['IN']), shell=True)

#%%
def build_paths(out_path, tiff_base, work_path, band_list):
    base = os.path.join(out_path, tiff_base)

    if not os.path.exists(base):
        os.makedirs(base)

    phs = {'VRT': {'OUT': os.path.join(work_path, tiff_base + '.vrt'),
                   'IN': ' '.join(band_list)},
           'TRAN': {'IN': os.path.join(work_path, tiff_base + '.vrt'),
                    'OUT': os.path.join(base, tiff_base + '_MTLstack.tif')}}
    
    return phs

#%%
def build_l8_list(work_path, tiff_base):
    return ['{}_SRB2.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB3.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB4.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB5.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB6.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB7.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_BTB10.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_PIXELQA.tif'.format(os.path.join(work_path, tiff_base))]

#%%
def build_tm_list(work_path, tiff_base):
    return ['{}_SRB1.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB2.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB3.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB4.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB5.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_SRB7.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_BTB6.tif'.format(os.path.join(work_path, tiff_base)),
            '{}_PIXELQA.tif'.format(os.path.join(work_path, tiff_base))]

#%%
def base_name(work_path):
    base = ''
    for tiff_file in os.listdir(work_path):
        if tiff_file[-9:] != '_SRB2.tif':
            continue

        base = tiff_file[:-9]
        break

    return base

#%%
def clean_up(work_path):
    for f in os.listdir(work_path):
        os.remove(os.path.join(work_path, f))

#%%
def find_tile_name(file):
    
    ds = gdal.Open(file)

    affine = extent_to_hv(ds.GetGeoTransform())

    ds = None
    
    return affine

#%%
def process_tile(file_q, prog_q, out_path, work_path):
    """Process a file from the queue"""
    proc = work_path[-1]
   
    while True:
        try:
            file = file_q.get()
            
            if file == 'KILL':
                prog_q.put('Killing process %s' % proc)
                break
            
            srpath, btpath = file
            print ('\n', srpath, '\n', btpath, '\n')
            prog_q.put('Process %s: Unpacking %s' % (proc, srpath))
            unpackage(srpath, work_path)
            prog_q.put('Process %s: Unpacking %s' % (proc, btpath))
            unpackage(btpath, work_path)
            
            tiff_base = base_name(work_path)

            if tiff_base[3] == '8':
                band_list = build_l8_list(work_path, tiff_base)
            else:
                band_list = build_tm_list(work_path, tiff_base)

           # out = os.path.join(out_path, find_tile_name(band_list[0]))

            pathing = build_paths(out_path, tiff_base, work_path, band_list)

            if os.path.exists(pathing['TRAN']['OUT']):
                clean_up(work_path)
                continue

            prog_q.put('Process %s: Building VRT stack for %s' % (proc, tiff_base))
            vrt(pathing)

            prog_q.put('Process %s: Calling Translate for %s' % (proc, tiff_base))
            translate(pathing)

#            prog_q.put('Process %s: Moving ancillery files for %s' % (proc, tiff_base))
#            if os.path.exists(pathing['GCP']['IN']):
#                shutil.copy(pathing['GCP']['IN'], pathing['GCP']['OUT'])
#            if os.path.exists(pathing['MTL']['IN']):
#                shutil.copy(pathing['MTL']['IN'], pathing['MTL']['OUT'])

            clean_up(work_path)
        except Exception as e:
            prog_q.put('Process %s: Hit an exception - %s' % (proc, e))
            prog_q.put('Killing process %s' % proc)
            clean_up(work_path)
            break

    os.rmdir(work_path)
    
#%%
def file_enqueue(path, q, worker_num):
    """Builds a queue of files to be processed"""

    for root, dirs, files in os.walk(path):
        for file in files:
            if file[-6:] == 'SR.tar':  #BT and SR
                
                a = os.path.join(root, file)    
                
                b = (a, a.replace("SR", "BT"))
                
                q.put( b )


    # for gzfile in os.listdir(path):
    #     if gzfile[-2:] != 'gz':
    #         continue
    #
    #     q.put(os.path.join(path, gzfile))
    for _ in range(worker_num):
        q.put('KILL')

#%%
def work_paths(worker_num, path):
    """Makes working directories for the multi-processing"""

    out = []
    for i in range(worker_num-1):
        new_path = os.path.join(path, 'espa_ard_working%s' % i)
        out.append(new_path)
        if not os.path.exists(new_path):
            os.mkdir(new_path)

    return out

#%%
def progress(prog_q, worker_num):
    count = 0
    while True:
        message = prog_q.get()

        # print(message)
        # sys.stdout.write(message)
        LOGGER.info(message)

        if message[:4] == 'Kill':
            count += 1
        if count >= worker_num - 1:
            break

#%%
def extent_to_hv(geoaffine):
    conus_uly = 3314805
    conus_ulx = -2565585

    ul_x, _, _, ul_y, _, _ = geoaffine

    h = int((ul_x - conus_ulx) / 150000)
    v = int((conus_uly - ul_y) / 150000)

    return 'h{0}v{1}'.format(h, v)

#%%
if __name__ == '__main__':
    # input_path = raw_input('Tarball inputs: ')
    # output_path = raw_input('Output directory: ')
    # num = raw_input('Number of workers: ')
    #if len(sys.argv) > 1:
    #    create_tiles(sys.argv[1], sys.argv[2], int(sys.argv[3]))

    #input_path = r'C:\Users\dzelenak\Workspace\LCMAP_Eval\ARD_h05v02'
    # input_path = '/lcmap_data/sites/ard_source/h04v01'
    #output_path = r'C:\Users\dzelenak\Workspace\LCMAP_Eval\Test_output'
    # output_path = '/lcmap_data/sites/washington/ARD/h04v01'
    # num = 10
    #
    # create_tiles(input_path, output_path, int(num))
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, help="Full path to the tarball inputs")
    parser.add_argument("-o", "--output", type=str, required=True, help="Full path to the output folder")
    parser.add_argument("-n", "--workers", type=int, required=False, default=20)

    args = parser.parse_args()

    input_path = args.input
    output_path = args.output
    num = args.workers

    create_tiles(input_path, output_path, int(num))