# load and display all movement data on html map of the area of interest including stations radius.
# extracts tag visits and colony visits csvs

### imports ###
import numpy as np
import pandas as pd
import scipy
import csv
import time
import sys
from pykml import parser
from glob import glob
import os
from datetime import datetime, timedelta
import folium
import webbrowser
import geojson
from pyproj import Proj, transform
import warnings
import mpu
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=DeprecationWarning)

stations = [[32.5128347589, 35.4531341842], [32.49208750481, 35.41152915349],
            [32.47712635287, 35.50302634681], [32.56955001832, 35.41751573809],
            [32.5520750428, 35.45852468563], [32.52783113203, 35.40896787929]]

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
    reads coordinates CSV, converts and measures process timimig
    preserves original data, creates new columns for converted coordinates
    clears redundant tag data
    keep indexing & grouping for future debugging and examinations
    """
    file_path = r"csv\localization_raw_export.csv"  # change if needed
    origin_df = pd.read_csv(file_path, usecols=['TAG', 'TIME', 'X', 'Y'])
    df = origin_df.copy()
    df = df.head(1000000000000)  # fast run for tests (100)
    start_time = time.perf_counter()

    df['TIME'] = pd.to_datetime(df['TIME'], unit='ms')
    df['TAG'] = df['TAG'].astype(str).str.replace('972006000', '')
    # convert coordinates in bulk for performance
    lon, lat = itm_to_wgs84_converter(df['X'].values, df['Y'].values)
    df['n_X'] = lon
    df['n_Y'] = lat
    finish = time.perf_counter()
    print(f"coordinates conversion took: {round(finish - start_time, 2)} seconds")

    df = df.sort_index()
    raw_data_df = df.groupby(['TAG', 'TIME', 'X', 'Y']).value_counts()
    raw_data_df.to_csv('converted_data.csv')
    return df, raw_data_df

def create_basemap():
    """
    creates a base map for data presentation using folium
    """
    basemap = folium.Map(location=[32.52563897389, 35.450283993], zoom_start=12)
    MAP_FILE = "base_map.html"
    style_function = lambda x: {'color': x['properties']['color'], 'weight': x['properties']['stroke-width']}
    return basemap, MAP_FILE, style_function

def add_stations(basemap, stations):
    """
    imports stations location into basemap, adding viewing properties
    """
    for i, station in enumerate(stations, start=1):
        folium.Circle(
            radius=1000, location=station, popup=f"Colony {i}", color="crimson", fill=False # station radius on map, needs to correlate value in fun: tag_time_in_station
        ).add_to(basemap)

def add_lines(basemap, points, style_function):
  """
  imports dictionary of grouped x,y locations by tag #
  generates 1 movement linestring for each tag by different color
  """
  lines = {"type": "FeatureCollection", "features": []}
  color_list = [
      'red', 'darkorange', 'gold', 'yellowgreen', 'forestgreen',
      'teal', 'royalblue', 'mediumblue', 'darkviolet', 'purple',
      'magenta', 'hotpink', 'darkred', 'lightsalmon', 'coral',
      'lightseagreen', 'lightskyblue', 'paleturquoise', 'mistyrose', 'lavender'
  ]
  
  # unique tag identifier dictionary and counter
  unique_tag_id = {}
  color_counter = 0
  for tag, route in points.items():
    if tag not in unique_tag_id:  # check if new tag
      unique_tag_id[tag] = color_counter
      color_counter = (color_counter + 1) % len(color_list)  # loop on color list 
    color = color_list[unique_tag_id[tag]] 

    for i in range(len(route)):
      if i < len(route) - 1:  # check if next point exists to avoid errors
        line_coords = [route[i][1:], route[i + 1][1:]]  # extract coordinates (ignore TIME slot here)
        feature = {
            "type": "Feature",
            "properties": {"color": color, "stroke-width": 0.5},
            "geometry": {"type": "LineString", "coordinates": line_coords},
        }
        lines["features"].append(feature)
  folium.GeoJson(lines, style_function=style_function).add_to(basemap)


def present_map(basemap, MAP_FILE):
    """
    assorts data and exports the map in a new html window"
    """
    basemap.save(MAP_FILE)
    if not os.path.isfile(MAP_FILE): # debugging for html issues
        print(f"error: File {MAP_FILE} not found, please check path")
        return

    url = f"file:///{os.getcwd()}/{MAP_FILE}"
    print(f"generated URL: {url}") # print URL
    webbrowser.open(url)

def analyze_tag_log(points_for_csv, stations, analysed_tags):
  """
  Compute movement data for each TAG by colony interactions.
  1- tag visits at each colony
  2- tag sleeps at each colony
"""
  movement_log = {}
  for tag, route in points_for_csv.items():
      tag_log = []
      for station in stations:
          time_in_station = tag_time_in_station(route, station)
          if time_in_station > 0.0: # min time threshold
              event_type = "visit" if time_in_station < 1.0 else "sleep"
              tag_log.append({"event": event_type, "duration [mins]": time_in_station, "inside colony #": station})
      if not tag_log:
          tag_log.append({"event": "no_visit", "duration [mins]": 0.0, "inside colony #": None})
      movement_log[tag] = tag_log

  movement_log_df = pd.DataFrame([(tag, log['event'], log['duration [mins]'], log['inside colony #']) 
                                  for tag, logs in movement_log.items() for log in logs], 
                                  columns=['tag #', 'event', 'duration [mins]', 'inside colony #'])
  movement_log_df.to_csv(analysed_tags, index=False)

def analyze_colony_log(points, stations, analysed_data):
  """
  Compute movement statistics for each colony by tag, recording event duration and colony.
  """
  colony_events = []
  for tag, route in points.items():
    for station in stations:
      time_in_station = tag_time_in_station(route, station)
      if time_in_station > 0.0:  # record any entrance to colony
        event_type = "sleep" if time_in_station > 1.0 else "visit"
        colony_events.append({
            "TAG": tag,
            "event": event_type,
            "duration [mins]": time_in_station,
            "colony_id": station, 
        })
        
  # create df from list of events
  colony_log_df = pd.DataFrame(colony_events, columns=['TAG', 'event', 'duration [mins]', 'colony_id'])
  colony_log_df.to_csv(analysed_data, index=False) 

def tag_time_in_station(route, station):
    """
    checks tags duration inside station. If tag wasn't at station, returns negative value.
    calculates distance between each point and station.
    """
    first_time_in_station = True
    station_entry_time = 0
    time_in_station = 0
    for entry in route:
        coord = (entry[2], entry[1])  # ensure coordinate tuple (lat, lon)
        if mpu.haversine_distance(coord, station) * 1000 < 1000: #  "* X < station radius". higher radius produces more sensetive results (change in map station radius accordingly)
            if first_time_in_station:
                station_entry_time = pd.to_datetime(entry[0])  # convert back to timestamp, resolves issues
                first_time_in_station = False
            else:
                time_in_station = (pd.to_datetime(entry[0]) - station_entry_time).total_seconds() / 60 # time in minutes
    return time_in_station

if __name__ == "__main__":
    start_time = time.perf_counter()
    df, raw_data_df = read_file()
    # map section
    points_for_map = {tag: list(zip(gdf['TIME'].astype(str), gdf['n_X'], gdf['n_Y'])) for tag, gdf in df.groupby('TAG')}
    basemap, MAP_FILE, style_function = create_basemap()
    add_stations(basemap, stations)
    add_lines(basemap, points_for_map, style_function)
    present_map(basemap, MAP_FILE)
    # csv section
    points_for_csv = {tag: list(zip(gdf['TIME'].astype(str), gdf['n_X'], gdf['n_Y'])) for tag, gdf in df.groupby('TAG')}
    analysed_tags = 'analysed_tags.csv'
    analyze_tag_log(points_for_csv, stations, analysed_tags)
    analysed_data = 'analysed_data.csv'
    analyze_colony_log(points_for_csv, stations, analysed_data)
    
    finish = time.perf_counter()
    print(f"Total script run time: {round(finish - start_time, 2)} seconds")
