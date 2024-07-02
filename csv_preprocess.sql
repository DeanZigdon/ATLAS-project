-- takes geojson preprocess.py csv and merge them to create a log with all surface type on each log.
--- display original extracted csv from qgis.geojson
--select * from rural_data;
--select * from urban_data;

--- check occurences for each surface type
--SELECT surface_type, COUNT("unknown") AS occurences
--FROM rural_data
--GROUP BY surface_type;

--SELECT surface_type, COUNT("unknown") AS occurences
--FROM urban_data
--GROUP BY surface_type;

-- shows the differences between surface_type classifications between urban and rural csv, based on TAG # & same time

SELECT rural_data.TAG, rural_data.TIME AS rural_time, rural_data.surface_type AS rural_surface_type,
       urban_data.TIME AS urban_time, urban_data.surface_type AS urban_surface_type
FROM rural_data
LEFT JOIN urban_data ON rural_data.TAG = urban_data.TAG AND rural_data.n_X = urban_data.n_X;

-- create combined table for both datasets (add water surface type from urban_data).
CREATE TABLE combined_data (TAG int, TIME text, X double, Y double, n_X double, n_Y double, geometry text, surface_type_combined text);

INSERT INTO combined_data (TAG, TIME, X, Y, n_X, n_Y, geometry, surface_type_combined)
SELECT 
	r.TAG, r.TIME, r.X, r.Y, r.n_X, r.n_Y, r.geometry,
    CASE WHEN u.surface_type = 'water' THEN u.surface_type ELSE r.surface_type END AS surface_type_combined -- add water surface type
FROM rural_data r  -- define allias "r"
LEFT JOIN urban_data u ON r.TAG = u.TAG AND r.n_X = u.n_X; -- define allias "u"

-- count occurences
SELECT surface_type_combined, COUNT(*) as occurences
FROM combined_data
-- WHERE surface_type_combined = 'water'  -- validate # of water occurences
GROUP BY  surface_type_combined 
order by surface_type_combined desc; 



--- to avoid permission issues, export csv manually (mark field separator as ','), else- use this:
--SELECT *
--INTO OUTFILE 'path\surface_type_combined.csv' -- change to local path
--FIELDS TERMINATED BY ','
--ENCLOSED BY '"'
--LINES TERMINATED BY '\n'
--FROM combined_data;
