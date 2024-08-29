# preprocess script- preproccessing all surface types in the area of interest, extracted from QGIS geojson files.
# this data is then proccessed by mysql script "csv_preprocess.sql"

import numpy as np
import pandas as pd
import csv
import time
import geopandas as gpd
from pyproj import Proj, transform
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)

def read_geojson_layers():
    """
    reads geojson files 
    """
    start_time = time.perf_counter()
    rural_gdf = gpd.read_file('qgis_data/landuse_surface.geojson')
    urban_gdf = gpd.read_file('qgis_data/natural_surface.geojson')
    water_gdf = gpd.read_file('qgis_data/natural_surface.geojson')
    # verify correct CRS
    target_crs = 'EPSG:4326'
    rural_gdf = rural_gdf.to_crs(target_crs)
    urban_gdf = urban_gdf.to_crs(target_crs)
    water_gdf = water_gdf.to_crs(target_crs)
    # filter only relevant columns
    rural_gdf = rural_gdf[['geometry', 'surface_type']]
    urban_gdf = urban_gdf[['geometry', 'surface_type']]
    water_gdf = water_gdf[['geometry', 'surface_type']]

    finish = time.perf_counter()
    print(f"Reading geojson took: {round(finish - start_time, 2)} seconds")
    return rural_gdf, urban_gdf, water_gdf

def save_individual_csvs(df, rural_gdf, urban_gdf, water_gdf):
    """
    extract and save surface type and geometry for each log
    """
    start_time = time.perf_counter()
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['n_X'], df['n_Y']))
    gdf.set_crs('EPSG:4326', inplace=True)

    # spatial join to each gdf, creates new csv
    rural_joined = gpd.sjoin(gdf, rural_gdf[['geometry', 'surface_type']], how='left', predicate='within')
    urban_joined = gpd.sjoin(gdf, urban_gdf[['geometry', 'surface_type']], how='left', predicate='within')
    water_joined = gpd.sjoin(gdf, water_gdf[['geometry', 'surface_type']], how='left', predicate='within')
    rural_joined.to_csv('rural_data.csv', index=False)
    urban_joined.to_csv('urban_data.csv', index=False)
    water_joined.to_csv('water_data.csv', index=False)

    finish = time.perf_counter()
    print(f"CSV extraction took: {round(finish - start_time, 2)} seconds")
    print("saved individual CSVs for rural, urban & water data")

def itm_to_wgs84_converter(X, Y):
    """
    receives x,y coordinates from df and converts to itm (lon, lat)
    """
    proj_wgs84 = Proj(init="epsg:4326")
    proj_itm = Proj(init="epsg:2039")
    lon, lat = transform(proj_itm, proj_wgs84, X, Y)
    return lon, lat

def read_file():
    """
    reads coordinates CSV, converts and measures process timing
    Preserves original data, creates new columns for converted coordinates
    Clears redundant tag data
    Keep indexing & grouping for future debugging and examinations
    """
    file_path = r"csv/localization_raw_export.csv"  # change if needed
    start_time = time.perf_counter()
    origin_df = pd.read_csv(file_path, usecols=['TAG', 'TIME', 'X', 'Y'])
    df = origin_df.copy()
    df = df.head(1000000000000)
    df['TIME'] = pd.to_datetime(df['TIME'], unit='ms')
    df['TAG'] = df['TAG'].astype(str).str.replace('972006000', '')
    start_time = time.perf_counter()
    # convert coordinates in bulk for performance
    lon, lat = itm_to_wgs84_converter(df['X'].values, df['Y'].values)
    df['n_X'] = lon
    df['n_Y'] = lat

    df = df.sort_index()
    raw_data_df = df.groupby(['TAG', 'TIME', 'X', 'Y']).value_counts()
    raw_data_df.to_csv('converted_data.csv')
    finish = time.perf_counter()
    print(f"coordinate conversion took: {round(finish - start_time, 2)} seconds")
    return df, raw_data_df

if __name__ == "__main__":
    start_time = time.perf_counter()
    df, raw_data_df = read_file()
    rural_gdf, urban_gdf, water_gdf = read_geojson_layers()
    save_individual_csvs(df, rural_gdf, urban_gdf, water_gdf)
    finish = time.perf_counter()
    print(f"tot process time took: {round(finish - start_time, 2)} seconds")