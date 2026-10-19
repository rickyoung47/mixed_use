from pathlib import Path
import geopandas as gpd
import pandas as pd
import json

ROOT = Path(__file__).resolve().parent.parent
SHP = ROOT / 'lecture05_Urban_Planning_Index' / 'shp'
OUT = Path(__file__).resolve().parent / 'data'
OUT.mkdir(exist_ok=True)
dong_path = SHP / 'LSMD_ADM_SECT_UMD_11_202609.shp'
bld_path = SHP / 'AL_D010_11_20261009' / 'AL_D010_11_20261009.shp'
land_path = next(SHP.glob('569*')) / 'UPIS_C_UQ111.shp'

dong = gpd.read_file(dong_path, encoding='cp949')[['EMD_CD', 'EMD_NM', 'geometry']]
bld = gpd.read_file(bld_path, encoding='cp949')
land = gpd.read_file(land_path, encoding='cp949')[['DGM_NM', 'LCLAS_CL', 'MLSFC_CL', 'geometry']]
print(f'loaded: dong={len(dong):,}, buildings={len(bld):,}, landuse={len(land):,}', flush=True)

# Use the building spatial index to identify exact intersecting pairs in one
# vectorized query (the source contains buildings across the entire country).
building_pairs = bld.sindex.query(dong.geometry, predicate='intersects')
hits = sorted(set(building_pairs[0].tolist()))
dong = dong.iloc[hits].copy()
print(f'dong polygons with buildings: {len(dong):,}', flush=True)
building_pairs = bld.sindex.query(dong.geometry, predicate='intersects')
print(f'building/dong intersection pairs: {building_pairs.shape[1]:,}', flush=True)

# Bring zoning polygons into the administrative-boundary CRS before clipping.
land = land.to_crs(dong.crs)
land_pairs = land.sindex.query(dong.geometry, predicate='intersects')
li, ldi = land_pairs[1], land_pairs[0]
shapely = __import__('shapely')
land_geom = shapely.intersection(shapely.make_valid(land.geometry.array.take(li)), dong.geometry.array.take(ldi))
land = land.iloc[li][['DGM_NM', 'LCLAS_CL', 'MLSFC_CL']].reset_index(drop=True)
land['geometry'] = gpd.GeoSeries(land_geom, crs=dong.crs)
land = gpd.GeoDataFrame(land, geometry='geometry', crs=dong.crs)
land = land[~land.geometry.is_empty & land.geometry.notna()].copy()

def classify(name):
    n = str(name or '')
    if '주거' in n: return '주거지역'
    if '상업' in n: return '상업지역'
    if '공업' in n: return '공업지역'
    if '녹지' in n: return '녹지지역'
    return '그 외'
land['zone'] = land['DGM_NM'].map(classify)
land = land[['DGM_NM', 'zone', 'geometry']]
land.geometry = land.geometry.simplify(3.0, preserve_topology=True)
print(f'clipped zoning polygons: {len(land):,}', flush=True)

dong.geometry = dong.geometry.simplify(2.0, preserve_topology=True)
dong = dong.to_crs(4326)
land = land.to_crs(4326)
for name, layer in [('dong',dong), ('landuse',land)]:
    path = OUT / f'{name}.geojson'
    layer.to_file(path, driver='GeoJSON', index=False)
    print(f'wrote {path.name}: {path.stat().st_size/1024/1024:.1f} MB', flush=True)
(OUT / 'summary.json').write_text(json.dumps({'buildings': int(pd.unique(building_pairs[1]).size)}, ensure_ascii=False))
