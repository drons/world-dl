[![codefactor.io](https://www.codefactor.io/repository/github/drons/world-dl/badge?style=flat-square)](https://www.codefactor.io/repository/github/drons/world-dl)
# Imagery download tool from web image services

## How to run

### Prepare environment
```
sudo apt install virtualenv python3-gdal
virtualenv -p python3 ./venv
```

### Clone and run

```
git clone https://github.com/drons/world-dl.git
cd world-dl.git
python3 ./world-dl.py --help
```

### Usage
```
usage: world-dl.py [-h] [-a {init,download}] -i INPUT -o OUTPUT [-s SCALE]
                   [-b BLOCK_SIZE] [-t TILE_SIZE]
                   [-c {JPEG,LZW,PACKBITS,DEFLATE,CCITTRLE,CCITTFAX3,CCITTFAX4,LZMA,ZSTD,LERC,LERC_DEFLATE,LERC_ZSTD,WEBP,NONE}]
                   [-m MASK] [-ov]

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
  -ov, --overviews      download overviews
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
