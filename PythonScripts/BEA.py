import requests
import pandas as pd
import os
import time
from IPython.display import clear_output

# Function to get the list of options for a given parameter
def get_options(params):
    endpoint = "https://apps.bea.gov/api/data/"
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'ParamValue' in data['BEAAPI']['Results']:
            if params['TargetParameter'] == 'Year':
                options = [{"Key": item['Key']}for item in data['BEAAPI']['Results']['ParamValue']]
                return options
            else:
                options = [
                {"Key": item['Key'], "Description": item['Desc']}
                for item in data['BEAAPI']['Results']['ParamValue']
                ]
            return options
        else:
            print("The 'ParamValue' key is not found in the response.")
            return []
    else:
        print("Failed to retrieve options, Status Code:", response.status_code)
        return []
    
    
# Function to get data for a given set of parameters
def getData(api_key, year,):
    endpoint = "https://apps.bea.gov/api/data/"
    params = {
        "UserID": api_key,
        "method": "GetData",
        "datasetname": 'REGIONAL',
        "TableName": 'CAGDP9',
        "GeoFIPS": 'MSA', 
        "LineCode": 1,
        "Year": year,
        "format": "JSON"
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        json_data = response.json()
        data_table = json_data['BEAAPI']['Results']['Data']
        df = pd.DataFrame(data_table)
        return df
    else:
        print("Failed to retrieve data")
        return pd.DataFrame()




if __name__ == '__main__':
    start_time = time.time()
    print('Running BEA API')
    os.makedirs('./BEA_Data', exist_ok=True)
    api_key = 'FFD1D8FA-E380-41F1-BDB5-F2DB18DA8792'
    # Passing in a range of years
    data_df = getData(api_key, range(2017, 2023))
    # Pivoting the dataframe to have 'GeoFips', 'GeoName', and 'TimePeriod' as rows and the values under 'DataValue' as columns
    pivot_data = data_df.pivot(index=['GeoFips', 'GeoName'], columns='TimePeriod', values='DataValue')
    # Resetting index to make 'GeoFips' and 'GeoName' as columns
    pivot_data.reset_index(inplace=True)
    # Renaming the columns for clarity
    pivot_data.columns.name = None
    pivot_data.columns = ['GeoFips', 'GeoName'] + [str(year) for year in range(2017, 2022 + 1)]
    pivot_data.to_csv(f'./BEA_Data/CAGDP9_2017-2023.csv', index=False)
    end_time = time.time()
    time_elapsed = end_time - start_time
    minutes = int(time_elapsed // 60)
    seconds = int(time_elapsed % 60)

    # Print formatted time
    print(f"Runtime: {minutes}:{seconds:02d}")