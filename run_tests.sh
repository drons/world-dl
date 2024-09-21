#!/bin/bash

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/bot/local/gdal301/lib:/home/bot/local/proj611/lib:/home/bot/local/openjpeg-2.3.0/lib
source venv/bin/activate

coverage run world-dl.py -h

coverage run --append world-dl.py -a init \
-s 65536 -b 2048 \
-i ./input/google_map.img \
-o ./out \
-m ./data/mask-no-ant-3857.tif \
-ml ./data/au.geojson

coverage run --append world-dl.py -a download \
-ov -u -c LZMA -t 512 \
-i ./input/google_map.img \
-o ./out

rm ./out/gmap_0_0.tif
rm ./out/gmap_0_2048.tif
echo "Hello" >> ./out/gmap_2048_2048.tif

coverage run --append world-dl.py -a merge -v \
-i ./input/google_map.img \
-o ./out || true && false

coverage run --append world-dl.py -a download \
-ov -u -c LZMA -t 512 \
-i ./input/google_map.img \
-o ./out

coverage run --append world-dl.py -a merge -v \
-i ./input/google_map.img \
-o ./out

coverage report --include world-dl.py
coverage html --include world-dl.py

