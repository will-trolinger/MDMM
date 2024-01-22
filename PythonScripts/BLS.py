import requests
import pandas as pd
import json
import time, os
from tqdm import tqdm


def get_bls_data_batch(series_ids_batch, api_key, start_year, end_year):
    # BLS API endpoint and headers setup
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    headers = {"Content-Type": "application/json"}

    # Preparing the data payload for the POST request, including series IDs and date range
    data = json.dumps({
        "seriesid": series_ids_batch,
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationKey": api_key
    })

    # Making the API request
    response = requests.post(url, data=data, headers=headers)
    response_json = response.json()

    # Collecting data from the response
    all_series_data = []
    if response_json['status'] == 'REQUEST_SUCCEEDED':
        for series in response_json['Results']['series']:
            series_id = series['seriesID']
            for item in series['data']:
                item['series_id'] = series_id  # Adding series_id to each data item
                all_series_data.append(item)
    else:
        print("Failed to fetch data for batch")
        print("Response:", response_json)

    # Converting the collected data into a DataFrame
    df = pd.DataFrame(all_series_data)
    if not df.empty:
        # Creating a combined year-period column for pivoting
        df['year_period'] = df['year'].astype(str) + "-" + df['periodName']
        # Pivoting the DataFrame to have years and periods as columns
        df = df.pivot_table(index='series_id', columns='year_period', values='value', aggfunc='first').reset_index()
        # Filling missing values with 0
        df.fillna(0, inplace=True)
    return df



def process_in_batches(series_ids, batch_size, api_key, name):
    # Processing the list of series IDs in batches
    all_data = pd.DataFrame()

    # Calculate the number of batches
    num_batches = (len(series_ids) + batch_size - 1) // batch_size

    # Wrap the range function with tqdm for a progress bar
    for i in tqdm(range(0, len(series_ids), batch_size), total=num_batches, desc=f"Downloading {name} Data"):
        batch = series_ids[i:i + batch_size]
        batch_data = get_bls_data_batch(batch, api_key, 2017, 2023)
        # Combining data from each batch into a single DataFrame
        all_data = pd.concat([all_data, batch_data], ignore_index=True)
        time.sleep(1)  # Throttling the requests by pausing for 1 second between batches

    return all_data


def sort_columns_by_date(df):
    # Sorting columns by date after excluding the 'series_id' column
    date_columns = df.columns.drop('series_id')
    date_columns_sorted = pd.to_datetime(date_columns, format='%Y-%B').sort_values()
    sorted_columns = ['series_id'] + date_columns_sorted.strftime('%Y-%B').tolist()
    return df[sorted_columns]

def create_annual_summariesEmployment(df):
    # Creating annual summaries (mean) for each series
    annual_summaries = {}
    for col in tqdm(df.columns, desc="Creating Annual Summaries for Employment Data"):
        if "-" in col:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            year = col.split("-")[0]
            # Calculating the mean for each year
            if year not in annual_summaries:
                annual_summaries[year] = numeric_col
            else:
                annual_summaries[year] += numeric_col

    # Calculate the mean instead of the sum
    for year in annual_summaries:
        annual_summaries[year] /= 12  # Assuming 12 periods per year

    annual_df = pd.DataFrame(annual_summaries)
    # Renaming columns to indicate annual average
    annual_df.columns = [f"{year}-Annual" for year in annual_df.columns]
    return annual_df


def interleave_annual_data(df, annual_df):
    # Interleaving annual data with monthly data
    for col in tqdm(annual_df.columns, desc="Integrating Annual Employment Data"):
        year = col.split("-")[0]
        if year != "2023":  # Skipping the year 2023
            december_col = f"{year}-December"
            loc = df.columns.get_loc(december_col)
            df.insert(loc + 1, col, annual_df[col])
    os.system('cls')
    return df

def create_annual_summariesWage(df):
    # Check if 'series_id' is in the index and reset it if necessary
    if 'series_id' not in df.columns:
        df = df.reset_index()

    # Extract 'series_id' for later use
    series_ids = df['series_id']

    # Creating annual summaries for each series
    annual_summaries = {}

    # Wrap the df.columns iteration with tqdm for a progress bar
    for col in tqdm(df.columns, desc="Creating Annual Summaries for Wage Data"):
        if "-" in col: 
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            year = col.split("-")[0]
            # Aggregating data annually
            if year not in annual_summaries:
                annual_summaries[year] = numeric_col
            else:
                annual_summaries[year] += numeric_col

    # Combining 'series_id' with annual data
    annual_df = pd.DataFrame(annual_summaries)
    annual_df['series_id'] = series_ids
    
    # Renaming columns to indicate annual aggregation
    annual_df.columns = [f"{col}-Annual" if col != 'series_id' else col for col in annual_df.columns]

    # Rearranging columns to bring 'series_id' to the front
    cols = annual_df.columns.tolist()
    cols.insert(0, cols.pop(cols.index('series_id')))
    annual_df = annual_df[cols]
    os.system('cls')
    return annual_df

def data():
    df = pd.read_csv('./BLS_Data/Employment_Data_Monthly_Annual.csv', low_memory=False, index_col=False)
    annual_cols = [col for col in df.columns if "Annual" in col] + ['series_id'] + [len(df.columns)-1]
    df = df[annual_cols]
    


if __name__ == "__main__":
    start_time = time.time()
    print('Running BLS API for Employment Data')
    os.makedirs('./BLS_Data', exist_ok =True)
    # First BLS Capture - Employment Data
    # API key and setup for fetching data
    api_key = "7fec3a74f560423a8aeb1a147eb24961"
    counties = pd.read_csv('./county_fips_master.csv', usecols=['fips'], low_memory=False)
    series = ["ENU" + f'{county:05d}' + "10010" for county in counties['fips']]
    batch_size = 50
    # Processing data
    df = process_in_batches(series, batch_size, api_key, 'Employment')
    pivot_df_sorted = sort_columns_by_date(df)
    annual_df = create_annual_summariesEmployment(pivot_df_sorted)
    final_df = interleave_annual_data(pivot_df_sorted, annual_df)
    # Exporting the final DataFrame to a CSV file
    final_df.to_csv("./BLS_Data/Employment_Data_Monthly_Annual.csv", index=False)
    print('Running BLS API for Wage Data')
    
    # Second BLS Capture - Wage Data
    series = ["ENU" + f'{county:05d}' + "50010" for county in counties['fips']]
    df = process_in_batches(series, batch_size, api_key, 'Wage')
    annual_df = create_annual_summariesWage(df)
    # Exporting the final DataFrame to a CSV file
    annual_df.to_csv('./BLS_Data/Wage_Data_Annual.csv', index=False)
    end_time = time.time()
    time_elapsed = end_time - start_time
    minutes = int(time_elapsed // 60)
    seconds = int(time_elapsed % 60)

    # Print formatted time
    print(f"Runtime: {minutes}:{seconds:02d}")




