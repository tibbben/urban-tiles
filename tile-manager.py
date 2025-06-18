#!/usr/bin/env python3
import os
import math
import time
import argparse
import requests
import geopandas as gpd
from shapely.geometry import box

# --- CONFIGURATION ---
KEY_FILE     = 'key.txt'
API_BASE_URL = 'https://api.howloud.com/tiles'
TILE_TYPE    = 'score'
TILE_ROOT    = 'tiles'
URBAN_PATH   = 'data/urban_boundary.geojson'
ZOOM_MIN     = 8
ZOOM_MAX     = 14

def load_api_key():
    with open(KEY_FILE, 'r') as f:
        return f.read().strip()

API_KEY = load_api_key()

# --- SLIPPY MAP UTILITIES ---
def latlon_to_tile(lat, lon, zoom):
    x = int((lon + 180) / 360 * 2**zoom)
    y = int((1 - math.log(math.tan(math.radians(lat)) +
             1 / math.cos(math.radians(lat))) / math.pi) / 2 * 2**zoom)
    return x, y

def tile_bounds(x, y, z):
    n = 2.0 ** z
    lon1 = x   / n * 360.0 - 180.0
    lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y   / n))))
    lon2 = (x+1) / n * 360.0 - 180.0
    lat2 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2*(y+1)/ n))))
    return [(lon1, lat2), (lon2, lat1)]  # [SW, NE]

def tile_intersects(x, y, z, geom):
    (lon1, lat1), (lon2, lat2) = tile_bounds(x, y, z)
    return geom.intersects(box(lon1, lat1, lon2, lat2))

# --- MAIN TILE PROCESSOR ---
def process_tiles(generate=False, request=False, max_downloads=0):
    print("=== Processing Tiles ===")
    if not generate and not request:
        print("Mode: Dry Run")
    elif generate:
        print("Mode: Generating Skeleton")
    else:
        print("Mode: Downloading Tiles")

    urban = gpd.read_file(URBAN_PATH).to_crs(epsg=4326)
    urban_union = urban.unary_union
    minx, miny, maxx, maxy = urban_union.bounds
    headers = {'x-api-key': API_KEY}
    download_count = 0

    for z in range(ZOOM_MIN, ZOOM_MAX + 1):  # z = zoom
        x_min, y_max = latlon_to_tile(miny, minx, z)
        x_max, y_min = latlon_to_tile(maxy, maxx, z)

        for y in range(y_min, y_max + 1):  # z = vertical index (latitude)
            for x in range(x_min, x_max + 1):  # x = horizontal index (Longitiude)
                if not tile_intersects(x, y, z, urban_union):
                    continue

                dir_path = os.path.join(TILE_ROOT, str(z), str(x))
                os.makedirs(dir_path, exist_ok=True)
                file_path = os.path.join(dir_path, f"{y}.png")
                url = f"{API_BASE_URL}/{TILE_TYPE}/{z}/{x}/{y}.png"

                if generate:
                    open(file_path, 'wb').close()
                    print(f"Generated: {file_path}")
                elif request:
                    if download_count >= max_downloads:
                        print(f"Reached max downloads: {max_downloads}")
                        return
                    try:
                        print(f"Requesting: {url}")
                        resp = requests.get(url, headers=headers, params={'x-api-key': API_KEY})
                        resp.raise_for_status()
                        with open(file_path, 'wb') as f:
                            f.write(resp.content)
                        print(f" → Saved: {file_path}")
                        download_count += 1
                    except Exception as e:
                        print(f"Failed {url}: {e}")
                    time.sleep(0.5) # make sure we don't go over the rate limit
                else:
                    print(f"URL:  {url}?x-api-key={API_KEY}")
                    print(f"Path: {file_path}")
                    print("-" * 60)

    print("Done.")

# --- ARGPARSE SETUP ---
if __name__ == '__main__':
    p = argparse.ArgumentParser(description="Tile dry-run / generate / download script")
    group = p.add_mutually_exclusive_group()
    group.add_argument('-g', '--generate', action='store_true',
                       help="Generate tile directory skeleton (placeholder .png files)")
    group.add_argument('--request', action='store_true',
                       help="Make real API requests to download tiles")
    p.add_argument('--max-downloads', type=int, default=5,
                   help="Limit number of downloads (only with --request)")
    args = p.parse_args()

    process_tiles(generate=args.generate, request=args.request, max_downloads=args.max_downloads)

