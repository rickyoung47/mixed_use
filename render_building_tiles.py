"""Render clipped Seoul building footprints into transparent web map tiles."""
from pathlib import Path
import math
import sys
import geopandas as gpd
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent.parent
SHP = ROOT / 'lecture05_Urban_Planning_Index' / 'shp'
OUT = Path(__file__).resolve().parent / 'tiles' / 'buildings'
TILE = 256
R = 6378137.0
MAX_LAT = 85.05112878

def tile_x(lon, z): return int((lon + 180) / 360 * (1 << z))
def tile_y(lat, z):
    lat = max(-MAX_LAT, min(MAX_LAT, lat))
    rad = math.radians(lat)
    return int((1 - math.asinh(math.tan(rad)) / math.pi) / 2 * (1 << z))
def tile_bounds(x, y, z):
    n = 1 << z
    minx = x / n * 2 * math.pi * R - math.pi * R
    maxx = (x + 1) / n * 2 * math.pi * R - math.pi * R
    maxy = math.pi * R - y / n * 2 * math.pi * R
    miny = math.pi * R - (y + 1) / n * 2 * math.pi * R
    return minx, miny, maxx, maxy
def pixel_ring(ring, bounds):
    minx, miny, maxx, maxy = bounds
    sx, sy = TILE / (maxx-minx), TILE / (maxy-miny)
    return [(round((x-minx)*sx), round((maxy-y)*sy)) for x, y, *_ in ring]
def polygons(geom):
    if geom.geom_type == 'Polygon': return [geom]
    if geom.geom_type == 'MultiPolygon': return list(geom.geoms)
    if geom.geom_type == 'GeometryCollection': return [p for g in geom.geoms for p in polygons(g)]
    return []

src = SHP / 'AL_D010_11_20261009' / 'AL_D010_11_20261009.shp'
dong_src = SHP / 'LSMD_ADM_SECT_UMD_11_202609.shp'
b = gpd.read_file(src, encoding='cp949', columns=['geometry']).to_crs(3857)
d = gpd.read_file(dong_src, encoding='cp949', columns=['geometry']).to_crs(3857)
print(f'Rendering {len(b):,} building footprints clipped to {len(d):,} legal-dong polygons', flush=True)
bi = b.sindex
di = d.sindex
dong_union = d.geometry.union_all()
building_geoms = b.geometry.values
dong_geoms = d.geometry.values
minlon, minlat, maxlon, maxlat = d.to_crs(4326).total_bounds
min_zoom, max_zoom = (int(v) for v in sys.argv[1:3]) if len(sys.argv) >= 3 else (10, 17)
for z in range(min_zoom, max_zoom + 1):
    x0, x1 = tile_x(minlon, z), tile_x(maxlon, z)
    y0, y1 = tile_y(maxlat, z), tile_y(minlat, z)
    total = 0
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            bounds = tile_bounds(x, y, z)
            tile_box = box(*bounds)
            if not dong_union.intersects(tile_box):
                continue
            candidates = bi.query(tile_box, predicate='intersects').tolist()
            if not candidates:
                continue
            tile_img = Image.new('RGBA', (TILE, TILE), (0, 0, 0, 0))
            draw = ImageDraw.Draw(tile_img)
            for idx in candidates:
                geom = building_geoms[idx]
                if geom.is_empty:
                    continue
                for poly in polygons(geom):
                    draw.polygon(pixel_ring(poly.exterior.coords, bounds), fill=(52, 78, 63, 218))
                    for hole in poly.interiors:
                        draw.polygon(pixel_ring(hole.coords, bounds), fill=(0, 0, 0, 0))
                    draw.line(pixel_ring(poly.exterior.coords, bounds), fill=(29, 51, 39, 225), width=1)
            mask = Image.new('L', (TILE, TILE), 0)
            md = ImageDraw.Draw(mask)
            for idx in di.query(tile_box, predicate='intersects'):
                geom = dong_geoms[idx]
                for poly in polygons(geom.intersection(tile_box)):
                    md.polygon(pixel_ring(poly.exterior.coords, bounds), fill=255)
                    for hole in poly.interiors:
                        md.polygon(pixel_ring(hole.coords, bounds), fill=0)
            tile_img.putalpha(Image.fromarray(np.minimum(np.array(tile_img.getchannel('A')), np.array(mask))))
            path = OUT / str(z) / str(x) / f'{y}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            tile_img.save(path, optimize=True)
            total += 1
    print(f'z{z}: {total} tiles', flush=True)
