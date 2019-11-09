"""
Imagery download tool from web image services
"""
from __future__ import print_function

import sys
import os
import shutil
import argparse
import datetime
import time
import sqlite3 as sqlite
from osgeo import gdal


def get_db(args):
    """:returns connection to download tasks DB"""
    db_file_name = os.path.join(args.output, 'block.db')
    return sqlite.connect(db_file_name)


def check_mask(mask, x, y, block_size, mask_scale, input_scale):
    """Return True if block have some valid data"""
    if mask is None:
        return True
    x0 = x * input_scale / mask_scale
    y0 = y * input_scale / mask_scale
    x1 = (x + block_size) * input_scale / mask_scale
    y1 = (y + block_size) * input_scale / mask_scale

    return mask[y0:y1, x0:x1].sum() > 0


def open_mask(args, input_ds):
    """
    Open nodata mask
    :returns mask and it's scale relative to input dataset
    """
    mask_ds = gdal.Open(args.mask)
    print('Mask dataset size', mask_ds.RasterXSize, 'x', mask_ds.RasterYSize)
    if mask_ds.RasterXSize >= input_ds.RasterXSize or \
            mask_ds.RasterYSize >= input_ds.RasterYSize:
        print('Too big mask image. Discard it.')
        mask_ds = None
    mask_scale = int(input_ds.RasterXSize / mask_ds.RasterXSize)
    if mask_scale != int(input_ds.RasterYSize / mask_ds.RasterYSize):
        print('Mask image have non uniform scale relative to input dataset')
        return 1
    mask = mask_ds.GetRasterBand(1).ReadAsArray()
    print('Mask is filled only by',
          int(100 * mask.sum() / (255.0 * mask_ds.RasterXSize * mask_ds.RasterYSize)), '%')
    mask_ds = None
    return mask, mask_scale


def run_init(args):
    """Initiate download tasks database"""
    input_ds = gdal.Open(args.input)
    print('Input dataset size', input_ds.RasterXSize, 'x', input_ds.RasterYSize)
    mask = None
    mask_scale = 0
    if args.mask is not None:
        mask, mask_scale = open_mask(args, input_ds)

    block_count_x = int(input_ds.RasterXSize // (args.block_size * args.scale))
    block_count_y = int(input_ds.RasterYSize // (args.block_size * args.scale))

    print('block_size', args.block_size)
    print('Out size',
          input_ds.RasterXSize // args.scale,
          input_ds.RasterYSize // args.scale)
    print('block_count_x, block_count, total',
          block_count_x, block_count_y,
          block_count_x*block_count_y)

    shutil.rmtree(args.output, ignore_errors=True)
    os.makedirs(args.output)
    conn = get_db(args)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE task
    (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input STRING,
    file_name STRING,
    file_url STRING,
    complete BOOL,
    inwork BOOL,
    block_size INT64,
    x INT64,
    y INT64,
    scale INT64,
    last_access DATETIME
    )""")
    valid_block_count = 0
    for iy in range(0, block_count_y):
        rows = []
        for ix in range(0, block_count_x):
            x = ix * args.block_size
            y = iy * args.block_size
            if not check_mask(mask, x, y, args.block_size, mask_scale, args.scale):
                continue
            row = (valid_block_count, args.input, 'gmap_{0}_{1}.tif'.format(x, y),
                   None, False, False, args.block_size,
                   x, y, args.scale, datetime.datetime.now())
            rows.append(row)
            valid_block_count = valid_block_count + 1
        cursor.executemany("INSERT INTO task VALUES "
                           "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        conn.commit()
    conn.close()
    print('Init done with', valid_block_count, 'data blocks queued from',
          block_count_x*block_count_y, '(',
          (100 * valid_block_count) / (block_count_x * block_count_y), '%)')
    return 0


def download_block(input_ds, args, file_name, block_size, x, y, scale):
    """
    Download one block from input datasource
    :param input_ds: Input datasource to download from
    :param args: module args
    :param file_name: output file name
    :param block_size: downloaded block size
    :param x: downloaded block X offset
    :param y: downloaded block Y offset
    :param scale: downloaded block scale
    :return: OK
    """
    start = time.time()
    out_path = os.path.join(args.output, file_name)
    creation_options = ['BIGTIFF=YES', 'TILED=YES',
                        'BLOCKXSIZE={}'.format(args.tile_size),
                        'BLOCKYSIZE={}'.format(args.tile_size),
                        'COMPRESS={}'.format(args.compress)]
    if args.overviews:
        creation_options.append('COPY_SRC_OVERVIEWS=YES')
    print(creation_options)
    ds = gdal.Translate(out_path, input_ds,
                        creationOptions=creation_options,
                        srcWin=[x * scale, y * scale,
                                block_size * scale, block_size * scale],
                        width=block_size, height=block_size,
                        callback=gdal.TermProgress)
    if ds is None:
        print('Can\'t download block {}, {} from {} to {}'
              .format(x, y, input_ds.GetDescription(), out_path))
        return None
    ds = None
    end = time.time()
    print('Download time', end - start, out_path)
    return 'OK'


def run_download(args):
    """Run download blocks from input datasource"""
    wms_cache_path = os.path.join(args.output, 'wms')
    gdal.SetConfigOption('GDAL_DEFAULT_WMS_CACHE_PATH', wms_cache_path)
    gdal.SetConfigOption('GDAL_TIFF_OVR_BLOCKSIZE', str(args.tile_size))
    input_ds = gdal.Open(args.input)
    print('Input dataset size', input_ds.RasterXSize, 'x', input_ds.RasterYSize)
    conn = get_db(args)
    while True:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT "
            "id, file_name, block_size, x, y, scale "
            "FROM task WHERE "
            "NOT complete "
            "LIMIT 1")
        row = cursor.fetchone()
        if row is None:
            break
        download_block(input_ds, args, row[1], row[2], row[3], row[4], row[5])
        cursor.execute('UPDATE task SET complete = 1 WHERE id = ?', [row[0]])
        conn.commit()
        # Do not allow to grow cache infinitely.
        # Drop it after each success download
        shutil.rmtree(wms_cache_path, ignore_errors=True)

    return 0


def get_bounds(input_ds):
    """
    Get datasource bounds in georeferenced units
    :param input_ds: input datasource
    :return: datasource bounds
    """
    gt = input_ds.GetGeoTransform()
    gx = []
    gy = []
    xarr = [0, input_ds.RasterXSize]
    yarr = [0, input_ds.RasterYSize]

    for px in xarr:
        for py in yarr:
            x = gt[0] + (px * gt[1]) + (py * gt[2])
            y = gt[3] + (px * gt[4]) + (py * gt[5])
            gx.append(x)
            gy.append(y)

    return [min(gx), min(gy), max(gx), max(gy)]


def run_merge(args):
    """Merge downloaded blocks into one VRT file"""
    input_ds = gdal.Open(args.input)
    print('Input dataset size', input_ds.RasterXSize, 'x', input_ds.RasterYSize)
    bounds = get_bounds(input_ds)
    print('Dataset bounds', bounds)

    conn = get_db(args)
    cursor = conn.cursor()

    complete_block_names = []
    for row in cursor.execute("SELECT file_name FROM task WHERE complete "):
        complete_block_names.append(os.path.join(args.output, row[0]))
    print('Found {} downloaded blocks'.format(len(complete_block_names)))

    gdal.BuildVRT(os.path.join(args.output, 'merge.img'),
                  complete_block_names,
                  outputBounds=bounds,
                  callback=gdal.TermProgress)

    return 0


def main(*argv):
    """Application entry point"""
    if not argv:
        argv = list(sys.argv)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-a', '--action', nargs=1, choices=['init', 'download', 'merge'],
        help='Action to start'
    )
    parser.add_argument(
        '-i', '--input', required=True,
        help='Input imagery service or XML config path '
             '(see https://gdal.org/drivers/raster/wms.html)'
    )
    parser.add_argument(
        '-o', '--output', required=True,
        help='output image path'
    )
    parser.add_argument(
        '-s', '--scale', type=int, default=1,
        help='output image scale'
    )
    parser.add_argument(
        '-b', '--block-size', type=int, default=4096,
        help='output image size'
    )
    parser.add_argument(
        '-t', '--tile-size', type=int, default=1024,
        help='output image tile size'
    )
    parser.add_argument(
        '-c', '--compress',
        choices=['JPEG', 'LZW', 'PACKBITS', 'DEFLATE', 'CCITTRLE',
                 'CCITTFAX3', 'CCITTFAX4', 'LZMA', 'ZSTD', 'LERC',
                 'LERC_DEFLATE', 'LERC_ZSTD', 'WEBP', 'NONE'], default='LZW',
        help='output image compression type '
             '(see https://gdal.org/drivers/raster/gtiff.html#creation-options)'
    )
    parser.add_argument(
        '-m', '--mask', default=None,
        help='select nodata mask image'
    )
    parser.add_argument(
        '-ov', '--overviews', default=False, action='store_true',
        help='download overviews')
    args = parser.parse_args(argv[1:])

    if args.action.count('init') > 0:
        exit(run_init(args))
    elif args.action.count('download') > 0:
        exit(run_download(args))
    elif args.action.count('merge') > 0:
        exit(run_merge(args))
    else:
        print('Unknown action', args.action)


if __name__ == '__main__':
    main()
