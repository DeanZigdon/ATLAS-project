# ATLAS-project
Data analysis project from my Msc, using real spatial animal movement (reverse GPS) using python,mySQL,QGIS,csv,html,powerBI.

this project goals are to extract, process and analyse movement of wildlife in predetermined area of interest (aoi).
the movement data derives from real life ATLAS systems (revese GPS) logs.
original data logs arrived in mysql format which were converted into CSV files.

1.this project begins with the file "dean final project.py"
in it, pre-processing is conducted for the datasets, in addition to display all movement data on html map of the aoi including stations radius.
it also extracts tag visits and colony visits csvs for further analysis.

2. "geojson preprocess.py" 
this file is running preproccessing of all surface types in the area of interest, extracted from QGIS geojson files.
this data is then proccessed by mysql script "csv_preprocess.sql"

3. "csv_preprocess.sql"
takes geojson preprocess.py csv and merge them to create "surface_type_combined.csv" with all occurences for each tag on each surface type.

4. "sum surface type timing.py"
preprocess script- creates csv with time over each surface type for all tags, deals with some sql->py convertion format issues.

5. "data analysis.pbix"
graphic representation of the results.



prior to running the script the following requirements are needed:
- internet access (opens html webmap).
- python packages installation:
numpy,pandas,scipy,time,os,sys,datetime,folium,geojson,glob,time,csv,pymkl,webbrowser,pyproj,warnings,matplotlib,mpu


the longest process in the project might take up to 20 seconds(on intel i7, 16gb RAM),
for testing and partial data representation uncomment: "#self.df = self.df.head(100)"

any bugs, improvement ideas and notes are always welcome!






