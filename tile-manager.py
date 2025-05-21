#!/usr/bin/env python3
import os
import math
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
ZOOM_MAX     = 16

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

# --- MODES ---
def dry_run():
    print("=== Dry Run: Listing API Requests ===\n")
    for y in os.listdir(TILE_ROOT):
        y_path = os.path.join(TILE_ROOT, y)
        if not os.path.isdir(y_path):
            continue
        for z in os.listdir(y_path):
            z_path = os.path.join(y_path, z)
            if not os.path.isdir(z_path):
                continue
            for fname in os.listdir(z_path):
                if not fname.endswith('.png'):
                    continue
                x = fname[:-4]
                url  = f"{API_BASE_URL}/{TILE_TYPE}/{z}/{y}/{x}.png?x-api-key={API_KEY}"
                path = os.path.join(TILE_ROOT, y, z, fname)
                print(f"URL:  {url}")
                print(f"Save: {path}")
                print("-" * 60)

def generate_skeleton():
    print("=== Generating directory skeleton ===")
    urban = gpd.read_file(URBAN_PATH).to_crs(epsg=4326)
    urban_union = urban.unary_union
    minx, miny, maxx, maxy = urban_union.bounds

    for z in range(ZOOM_MIN, ZOOM_MAX + 1):
        print(f" Zoom {z}…")
        x_min, y_max = latlon_to_tile(miny, minx, z)
        x_max, y_min = latlon_to_tile(maxy, maxx, z)
        for y in range(y_min, y_max + 1):
            for x in range(x_min, x_max + 1):
                if tile_intersects(x, y, z, urban_union):
                    dir_path = os.path.join(TILE_ROOT, str(y), str(z))
                    os.makedirs(dir_path, exist_ok=True)
                    open(os.path.join(dir_path, f"{x}.png"), 'wb').close()
    print("Done.")

def download_tiles(max_downloads):
    print("=== Downloading tiles ===")
    headers = {'x-api-key': API_KEY}
    count = 0

    for y in os.listdir(TILE_ROOT):
        y_path = os.path.join(TILE_ROOT, y)
        if not os.path.isdir(y_path):
            continue
        for z in os.listdir(y_path):
            z_path = os.path.join(y_path, z)
            if not os.path.isdir(z_path):
                continue
            for fname in os.listdir(z_path):
                if not fname.endswith('.png'):
                    continue
                if count >= max_downloads:
                    print(f"Reached download limit ({max_downloads}).")
                    return
                x = fname[:-4]
                url  = f"{API_BASE_URL}/{TILE_TYPE}/{z}/{y}/{x}.png"
                path = os.path.join(TILE_ROOT, y, z, fname)
                print(f"Requesting: {url}")
                try:
                    resp = requests.get(url, headers=headers, params={'x-api-key': API_KEY})
                    resp.raise_for_status()
                    with open(path, 'wb') as f:
                        f.write(resp.content)
                    print(f" → Saved: {path}")
                    count += 1
                except Exception as e:
                    print(f"Failed {url}: {e}")
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

    if args.generate:
        generate_skeleton()
    elif args.request:
        download_tiles(args.max_downloads)
    else:
        dry_run()
