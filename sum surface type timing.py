# preprocess script- creates csv with time over each surface type for all tags

import pandas as pd
from datetime import datetime
import time

def read_file():
    """ 
    reads the csv exported from sql (surface_type_combined.csv)
    counts the duration each tag has spent over every surface type and saves it in a new csv.
    """
    file_path = "csv/surface_type_combined.csv"  # change if needed
    start_time = time.perf_counter()

    df = pd.read_csv(file_path, delimiter=',', quotechar='"') # removes quotes and delimiters from sql, wont run otherwise
    df.columns = [col.strip() for col in df.columns] # strip columns from sql, removes extra quotes, wont run otherwise 
    df['TIME'] = pd.to_datetime(df['TIME'], format='%Y-%m-%d %H:%M:%S.%f') # convert time to datetime format for calc
    
    tag_times = {} # create dictionary to store time for each tag value
    for tag in df['TAG'].unique():
        tag_times[tag] = {
            'time_urban [mins]': 0,
            'time_rural [mins]': 0,
            'time_water [mins]': 0,
            'time_unknown [mins]': 0
        }
    
    for tag in df['TAG'].unique():
        tag_df = df[df['TAG'] == tag].sort_values(by='TIME').reset_index(drop=True) # drop true = reset index by time
        
        for i in range(len(tag_df) - 1):
            current_row = tag_df.iloc[i]
            next_row = tag_df.iloc[i + 1]
            
            time_diff = (next_row['TIME'] - current_row['TIME']).total_seconds() / 60.0  # convert to mins
            
            if time_diff < 0: # filter negative time values
                print(f"error: negative time diff for TAG {tag} at index {i}. Skipping this interval")
                continue
            
            # sum up the time for each surface type
            if current_row['surface_type_combined'] == 'urban':
                tag_times[tag]['time_urban [mins]'] += time_diff
            elif current_row['surface_type_combined'] == 'rural':
                tag_times[tag]['time_rural [mins]'] += time_diff
            elif current_row['surface_type_combined'] == 'water':
                tag_times[tag]['time_water [mins]'] += time_diff
            else:
                tag_times[tag]['time_unknown [mins]'] += time_diff
    
    # convert summed times to a df
    results = pd.DataFrame.from_dict(tag_times, orient='index').reset_index()
    results.rename(columns={'index': 'TAG'}, inplace=True)
    
    output_file = "surface_time.csv"
    results.to_csv(output_file, index=False)
    finish = time.perf_counter()
    print(f"surface_type_timing took: {round(finish - start_time, 2)} seconds")
    return results, output_file

df_result, output_file = read_file()
print(f"surface type timing saved to: {output_file}")
