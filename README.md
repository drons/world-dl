[![codefactor.io](https://www.codefactor.io/repository/github/drons/world-dl/badge?style=flat-square)](https://www.codefactor.io/repository/github/drons/world-dl)
[![codecov](https://codecov.io/gh/drons/world-dl/branch/master/graph/badge.svg)](https://codecov.io/gh/drons/world-dl)
[![Build Status](https://github.com/drons/world-dl/actions/workflows/main.yml/badge.svg?branch=master)](https://github.com/drons/world-dl/actions/workflows/main.yml)
# Imagery download tool from web image services

## How to run

### Clone project
```
git clone https://github.com/drons/world-dl.git
cd world-dl.git
```

### Prepare environment
```
sudo apt-get install virtualenv python3-gdal
virtualenv -p /usr/bin/python3 --system-site-packages ./venv
source ./venv/bin/activate
pip install --upgrade tqdm requests numpy argparse pysqlite3
```

### Run

```
python world-dl.py --help
```

### Usage
```
usage: world-dl.py [-h] [-a {init,download,merge}] -i INPUT -o OUTPUT
                   [-s SCALE] [-b BLOCK_SIZE] [-t TILE_SIZE]
                   [-c {JPEG,LZW,PACKBITS,DEFLATE,CCITTRLE,CCITTFAX3,CCITTFAX4,LZMA,ZSTD,LERC,LERC_DEFLATE,LERC_ZSTD,WEBP,NONE}]
                   [-m MASK] [-ov] [-u] [-v] [-p PROXY] [-k]

optional arguments:
  -h, --help            show this help message and exit
  -a {init,download,merge}, --action {init,download,merge}
                        Action to start
  -i INPUT, --input INPUT
                        Input imagery service or XML config path (see
                        https://gdal.org/drivers/raster/wms.html)
  -o OUTPUT, --output OUTPUT
                        output image path
  -s SCALE, --scale SCALE
                        output image scale
  -b BLOCK_SIZE, --block-size BLOCK_SIZE
                        output image size
  -t TILE_SIZE, --tile-size TILE_SIZE
                        output image tile size
  -c {JPEG,LZW,PACKBITS,DEFLATE,CCITTRLE,CCITTFAX3,CCITTFAX4,LZMA,ZSTD,LERC,LERC_DEFLATE,LERC_ZSTD,WEBP,NONE}, --compress {JPEG,LZW,PACKBITS,DEFLATE,CCITTRLE,CCITTFAX3,CCITTFAX4,LZMA,ZSTD,LERC,LERC_DEFLATE,LERC_ZSTD,WEBP,NONE}
                        output image compression type (see
                        https://gdal.org/drivers/raster/gtiff.html#creation-
                        options)
  -m MASK, --mask MASK  select nodata mask image
  -ml MASK_LAYER, --mask-layer MASK_LAYER select nodata mask vector layer  
  -ov, --overviews      download overviews
  -u, --upload          upload image blocks to https://bashupload.com
  -v, --verify          check file hash before merge
  -p PROXY, --proxy PROXY
                        Run download via http proxy (format host:port)
  -k, --keep-cache      Keep tile cache after block complete
```

## Examples

Init download tasks database
```
python world-dl.py -a init \
-s 16384 -b 1024 \
-i ./input/google_map.img \
-o ./out \
-m ./data/mask-no-ant-3857.tif
```

Run download
```
python world-dl.py -a download \
-ov -c LZMA -t 512 \
-i ./input/google_map.img \
-o ./out
````
You can interrupt the download, and start it again

Merge images into VRT file
```
python world-dl.py -a merge \
-i ./input/google_map.img \
-o ./out
````
