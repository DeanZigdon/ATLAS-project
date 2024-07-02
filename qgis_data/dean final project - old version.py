# old version, using classes,lambda, more libraries, basic results.
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
import pyproj
import warnings 
import mpu 
warnings.simplefilter(action='ignore', category=FutureWarning) 
warnings.simplefilter(action='ignore', category=DeprecationWarning) 

# part 1, loading and pre process of data.
class ColonyParser:
    def __init__(self, file_path, output_dir):
        """ it recivecs wanted file path, exports wanted columns into CSV."""
        self.file_path = file_path
        self.output_dir = output_dir
        self.df = None
        
    def read_file(self):
        """ 
        pre-process of data.
        - the timestamp in the csv is a unix counter in miliseconds since 01-01-1970,
        this function syncs and convert timestamp into readable date format.
        - calls coordinates converter function.
        - sets indexes and priorities tag, time and columns respectivley.
        """
        self.df = pd.read_csv(self.file_path, usecols=['TAG','TIME','X','Y'])
        self.df = self.df.head(100)                                                 # fast run for tests
        self.df['TIME'] = pd.to_datetime(self.df['TIME'],unit='ms')
        self.df['TAG'] = self.df['TAG'].astype(str).str.replace('972006000','')
        results = self.df[['X', 'Y']].apply(lambda g: self.itm_to_wgs84_converter(g['X'], g['Y']), axis=1)
        self.df['X'] = list(map(lambda x: x[0], results))
        self.df['Y'] = list(map(lambda x: x[1], results))
        self.df.set_index(['TAG','TIME'],inplace= True)
        self.df = self.df.sort_index()
        self.df = self.df.groupby(['TAG','TIME','X','Y']).value_counts()
        
    def parse_data(self):
        """overall instruction to exported file."""
        self.read_file()  
        self.df.to_csv(self.output_dir)

    def itm_to_wgs84_converter (self, X,Y):
        """receives x,y coordinates from df and converts to itm(lon,lat)"""
        proj_wgs84 = pyproj.Proj(init="epsg:4326")
        proj_itm = pyproj.Proj(init="epsg:2039")
        lon,lat = pyproj.transform(proj_itm,proj_wgs84, X, Y)
        return lon,lat
    
    def get_points(self) :
        """ creates tuple of lists for 'add_lines' function for every different tag number """
        points = {}
        for entry in self.df.items():
            if not entry[0][0] in points:
                points[entry[0][0]] = []
                points[entry[0][0]].append((entry[0][1],list(entry[0][2:])))                    
            else:
                points[entry[0][0]].append((entry[0][1],list(entry[0][2:]))) 
        return points            

# part 2 - map creation
class MapPresentor:
    def __init__(self):
        """creates basemap mainframe for data presentation"""
        self.basemap = folium.Map(location=[32.52563897389, 35.450283993], zoom_start=12)
        self.MAP_FILE = "base_map.html"
        self.style_function = lambda x: {
            'color' : x['properties']['color'],'weight' : x['properties']['stroke-width']}
        return
    
    def add_stations(self, stations : list):
        """ importing stations location list into basemap with viewing details by numbering order """
        for i,station in enumerate(stations,start=1):
            folium.Circle(
                radius=50, location= station,
                popup=f"colony {i}",color="crimson",fill=False,).add_to(self.basemap)
        return
    
    def add_lines(self, points : dict):
        """"importing dictionary of groupped x,y locations by tag, generates 1 movement linestring for each tag #."""
        lines = {"type":"FeatureCollection","features": []}
        for tag, route in points.items():
            for index in range(len(route) - 1):
                line_coords = [route[index][1],route[index + 1][1]]
                feature = {"type":"Feature","properties":\
                          {"color": "crimson", "stroke-width": 0.5},\
                          "geometry":{"type":"LineString","coordinates": line_coords}}   
                lines["features"].append(feature)
        folium.GeoJson(lines, style_function=self.style_function).add_to(self.basemap)
        return
    
    def present_map(self):
        """"assorts data and exports the map in a new html window"""
        self.basemap.save(self.MAP_FILE) 
        self.basemap.add_child(folium.LatLngPopup())
        url = 'file://' + os.getcwd() + '/' + self.MAP_FILE  
        webbrowser.open(url)
        
# part 3 - data analysiss
class df_analysiss:
    def __init__(self,analysed_data,colony_df,analysed_tags):
        """constructor function
        calculates and imports statistical analysis into designated CSV"""
        self.colony_df = colony_df
        self.analysed_data = analysed_data
        self.analysed_tags = analysed_tags
        
    def analyze_tag_log(self,points):
        """"compute movement statisics for each TAG by colony interactions.
        1- tag visits at each colony
        2- tag sleeps at each colony """
        self.colony_df
        movement_log = {}
        for station in stations:
            for tag,route in points.items():
                time_in_station = self.tag_time_in_station(route,station)
                if time_in_station > 1.0:
                    movement_log[tag] = "sleep"
                elif (time_in_station <1.0) and (time_in_station > 0.0):
                    movement_log[tag] = "visit"
                else: 
                    movement_log[tag] = "no_visit"
        movement_log = pd.DataFrame.from_dict(movement_log, orient = "index",columns = ['event'])
        movement_log.index.name= 'station'
        movement_log.to_csv(self.analysed_tags)    
        
    def analyze_colony_log(self,points):
        """compute movement statistics for each colony by tag"""
        self.colony_df
        tag_log = {}
        for tag,route in points.items():
            for station in stations:
                time_in_station = self.tag_time_in_station(route,station)
                if time_in_station > 1.0:
                    tag_log[tag] = "sleep"
                elif (time_in_station <1.0) and (time_in_station > 0.0):
                    tag_log[tag] = "visit"
                else: 
                    tag_log[tag] = "no_visit"
        colony_logdf = pd.DataFrame.from_dict(tag_log, orient = "index",columns = ['event'])
        colony_logdf.index.name= 'TAG'
        colony_logdf.to_csv(self.analysed_data)
         
    """checks tags duration inside station, if tag wasn't at station- return negative value
    calculates distance between each point and station"""
    def tag_time_in_station(self,route,station):
           first_time_in_station = True
           station_entry_time = 0
           time_in_station = 0
           for entry in route :
              if mpu.haversine_distance(entry[1],station)* 1000 < 50:
                  if first_time_in_station:
                      station_entry_time = entry[0]
                      first_time_in_station = False
                  else:
                      time_in_station = (entry[0] - station_entry_time) / 60
           return time_in_station

stations = [[32.5128347589, 35.4531341842],[32.49208750481, 35.41152915349],
            [32.47712635287, 35.50302634681],[32.56955001832, 35.41751573809],
            [32.5520750428, 35.45852468563],[32.52783113203, 35.40896787929],]
plot_color_list =["crimson","#72A0C1","#0000ff","#B9F2FF","#006400","Cultured","Cyan Cobalt Blue","#8B008B","#966FD6","#9B870C","#4A646C"]

file_path = r"localization_raw_export.csv"
exported_file = r"exported_file.csv" 
analysed_data = r"analysed_data.csv"
analysed_tags = r"analysed_tags.csv"
if __name__ == '__main__':
    colony_parser = ColonyParser(file_path, output_dir=exported_file)
    colony_parser.parse_data()
    colony_df = colony_parser.df
    points = colony_parser.get_points()
    print('preprocess localization.csv exported')
    map_pr = MapPresentor()
    map_pr.add_stations(stations)
    map_pr.add_lines(colony_parser.get_points())
    map_pr.present_map()
    print('opening map,internet connection is required')
    data_analysis = df_analysiss(analysed_data,colony_df,analysed_tags)
    data_analysis.analyze_colony_log(points)
    data_analysis.analyze_tag_log(points)
    print('analysed data exported')