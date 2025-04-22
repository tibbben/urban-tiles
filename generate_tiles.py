import os
import math
import geopandas as gpd
from shapely.geometry import box

# --- Config ---
ZOOM_MIN = 9
ZOOM_MAX = 16
URBAN_PATH = "data/urban_boundary.geojson"
TILE_ROOT = "tiles"

# --- Load urban boundary ---
urban = gpd.read_file(URBAN_PATH).to_crs(epsg=4326)
urban_union = urban.unary_union

# --- Slippy map tile functions ---
def latlon_to_tile(lat, lon, zoom):
    x_tile = int((lon + 180) / 360 * (2 ** zoom))
    y_tile = int((1 - math.log(math.tan(math.radians(lat)) +
                 1 / math.cos(math.radians(lat))) / math.pi) / 2 * (2 ** zoom))
    return x_tile, y_tile

def tile_bounds(x, y, z):
    n = 2.0 ** z
    lon1 = x / n * 360.0 - 180.0
    lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lon2 = (x + 1) / n * 360.0 - 180.0
    lat2 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return [(lon1, lat2), (lon2, lat1)]  # [SW, NE]

def tile_intersects(x, y, z, geom):
    (lon1, lat1), (lon2, lat2) = tile_bounds(x, y, z)
    tile_poly = box(lon1, lat1, lon2, lat2)
    return geom.intersects(tile_poly)


# --- Main tile generation loop ---
for z in range(ZOOM_MIN, ZOOM_MAX + 1):
    print(f"Zoom level {z}...")

    # Get bounding box of the urban union geometry
    minx, miny, maxx, maxy = urban_union.bounds

    # Convert bounding box corners to tile coordinates
    x_min, y_max = latlon_to_tile(miny, minx, z)  # lower-left
    x_max, y_min = latlon_to_tile(maxy, maxx, z)  # upper-right

    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            if tile_intersects(x, y, z, urban_union):
                tile_dir = f"{TILE_ROOT}/{z}/{x}"
                os.makedirs(tile_dir, exist_ok=True)
                tile_path = f"{tile_dir}/{y}.png"
                with open(tile_path, "wb") as f:
                    f.write(b"")  # Placeholder or actual tile data


