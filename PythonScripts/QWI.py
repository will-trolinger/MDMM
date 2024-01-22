from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import time, json, os, shutil
from tqdm import tqdm
import pandas as pd


def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return os.listdir(directory_path) == []

def scrape_years_and_metros():
    min_most_recent_year = 9999
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensures the browser runs in headless mode
    chrome_options.add_argument('window-size=1920x1080')

    metro_year = {}
    driver = webdriver.Chrome(options=chrome_options)

    url = "https://ledextract.ces.census.gov/qwi/all"
    driver.get(url)
    wait = WebDriverWait(driver, 20)

    # Firm Characteristics
    firm_characteristics_tab = wait.until(EC.element_to_be_clickable((By.ID, "tabs_tablist_firm_char_tab")))
    firm_characteristics_tab.click()
    firm_age_radio_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='radio'][@name='fas'][@value='fa']")))
    firm_age_radio_button.click()
    all_ages = wait.until(EC.element_to_be_clickable((By.NAME, "firmage_all")))
    all_ages.click(); all_ages.click()

    one_year = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox'][@name='firmage'][@value='1']")))
    one_year.click()
    two_three_years = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox'][@name='firmage'][@value='2']")))
    two_three_years.click()
    four_five_years = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox'][@name='firmage'][@value='3']")))
    four_five_years.click()

    # Worker Characteristics
    worker_characteristics_tab = driver.find_element(By.ID, "tabs_tablist_worker_char_tab")
    worker_characteristics_tab.click()
    sex_education_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='radio'][@name='worker_xing'][@value='se']")))
    sex_education_button.click()

    edu_buttons = [
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        for xpath in [
            "//input[@type='checkbox'][@name='worker_se_education'][@value='E0']",
            "//input[@type='checkbox'][@name='worker_se_education'][@value='E1']",
            "//input[@type='checkbox'][@name='worker_se_education'][@value='E2']",
            "//input[@type='checkbox'][@name='worker_se_education'][@value='E3']",
            "//input[@type='checkbox'][@name='worker_se_education'][@value='E4']",
        ]
    ]
    for btn in edu_buttons: btn.click()

    # Geography
    geo_tab = wait.until(EC.element_to_be_clickable((By.ID, "tabs_tablist_area_tab")))
    geo_tab.click()
    time.sleep(0.1)
    checkbox = wait.until(EC.element_to_be_clickable((By.NAME, "areas_list_all")))
    checkbox.click()
    time.sleep(0.1)
    checkbox.click()

    try:
        container = driver.find_element(By.ID, "dijit_layout_ContentPane_2")
        states = container.find_elements(By.CSS_SELECTOR, "li.vtab")

        # Wrap the loop with tqdm
        for state in tqdm(states[1:], desc="Processing States"):  # Skip the first item (United States)
            state_div = state.find_element(By.CSS_SELECTOR, "div")
            state_div.click(); time.sleep(0.1)

            metro_div = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Metro/Micropolitan Areas']")))
            metro_div.click(); time.sleep(0.5)

            checkboxes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='checkbox' and @name='areas_list_M']")))
            for checkbox in checkboxes:
                if checkbox.is_displayed() and checkbox.is_enabled(): checkbox.click()
            time.sleep(0.25)

            link = wait.until(EC.element_to_be_clickable((By.ID, "tabs_tablist_quarters_tab")))
            link.click(); time.sleep(0.1)

            details_element = driver.find_element(By.CSS_SELECTOR, "details[data-source-name='areas_list_M']")
            metro_values = [element.get_attribute("data-value") for element in details_element.find_elements(By.CSS_SELECTOR, "li[data-value]")]
            time.sleep(0.25)

            try:
                table = driver.find_element(By.CSS_SELECTOR, "table.CheckGrid")
                most_recent_year = None
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                for row in rows:
                    year_cells = row.find_elements(By.CSS_SELECTOR, "td[abbr]")
                    if year_cells:
                        year = year_cells[0].get_attribute("abbr")
                        checkboxes = row.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                        if len(checkboxes) == 4 and all(not checkbox.get_attribute("disabled") for checkbox in checkboxes):
                            most_recent_year = year; break

                if most_recent_year:
                    metro_year.setdefault(most_recent_year, []).extend(metro_values)
                    if int(most_recent_year) < min_most_recent_year:
                        min_most_recent_year = int(most_recent_year)
            except Exception as e:
                print(f"Error processing state {state_div.text}: {str(e)}")
            finally:
                time.sleep(0.5)

            # Reset Geographies
            geography_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Geography']")))
            geography_button.click()
            reset_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Reset']")))
            reset_button.click()
            time.sleep(0.25)
            us_div = states[0].find_element(By.CSS_SELECTOR, "div")
            us_div.click()
            time.sleep(0.1)
            checkbox = wait.until(EC.element_to_be_clickable((By.NAME, "areas_list_all")))
            checkbox.click()
            time.sleep(0.1)
            checkbox.click()

    except TimeoutException:
        print("The checkbox or metro section was not clickable within the expected time.")
    finally:
        driver.quit()
        os.system('clear')

    create_uploadFile(metro_year)

def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    return os.listdir(directory_path) == []

def create_uploadFile(metro_year):
    print('Creating QWI Settings Files')
    # Determine directories
    isUploadDirEmpty = create_directory("./Upload")
    isTempDirNewOrEmpty = create_directory("./TempUpload")
    
    # Choose directory based on whether Upload is empty
    dir = "./Upload" if isUploadDirEmpty else "./TempUpload"

    for year, metros in metro_year.items():
        data = {
            "selected_areas": {"geo_ids": metros},
            "firm_attributes": {
                "naics_level": "naics2", "selected_naics": ["00"], "ownership": "op", "fas": "fa",
                "firm_age": ["0","1", "2", "3"], "firm_size": ["0"]},
            "worker_attributes": {"group": "se", "attr1": ["0"], "attr2": ["EO","E1", "E2", "E3", "E4"]},
            "indicators": ["Emp"], "quarters": [f"{year}.1", f"{year}.2", f"{year}.3", f"{year}.4"], "export_labels": True, "worker_xing": "se"}
        file_name = f"./{dir}/output_{year}.qwi"
        with open(file_name, "w") as file: json.dump(data, file, indent=4)
    
    min_year = int(min(metro_year.keys()))
    max_year = int(max(metro_year.keys()))
    all_quarters = [f"{year}.{q}" for year in range(min_year, max_year + 1) for q in range(1, 5)]
    usa_data = {
        "selected_areas": {"geo_ids": ["00"]},  # Using GEOID '00'
        "firm_attributes": {
            "naics_level": "naics2", "selected_naics": ["00"], "ownership": "op", "fas": "fa",
            "firm_age": ["0","1", "2", "3"], "firm_size": ["0"]},
        "worker_attributes": {"group": "se", "attr1": ["0"], "attr2": ["EO","E1", "E2", "E3", "E4"]},
        "indicators": ["Emp"], "quarters": all_quarters, "export_labels": True, "worker_xing": "se"}
        
    usa_file_path = os.path.join("./Upload", "USA_DATA.qwi")
    with open(usa_file_path, "w") as file:
        json.dump(usa_data, file, indent=4)

    # Check for new data and download if necessary
    if isTempDirNewOrEmpty or (isUploadDirEmpty and os.listdir('./QWI_Data') == []):
        download_file()

def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def check_settings_file():
    print('Comparing QWI Settings Files')
    settings_dir = "./Upload"
    temp_settings_dir = "./TempUpload"

    settings_files_contents = {f: read_json(os.path.join(settings_dir, f))
                               for f in os.listdir(settings_dir) 
                               if os.path.isfile(os.path.join(settings_dir, f)) and not f.startswith("USA")}
    all_matched = True  
    for temp_file in os.listdir(temp_settings_dir):
        temp_file_path = os.path.join(temp_settings_dir, temp_file)
        if os.path.isfile(temp_file_path):  # Ensure it's a file
            temp_file_content = read_json(temp_file_path)

            # Compare the file content with existing settings
            if temp_file_content in settings_files_contents.values():
                os.remove(temp_file_path)  # Delete the temp file if a match is found
            else:
                shutil.move(temp_file_path, os.path.join(settings_dir, temp_file))  # Move unmatched file
                all_matched = False  # Indicate that a new file was found

    return all_matched

def download_file():
    download_dir = os.path.abspath("./QWI_Data")
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    chrome_options.add_argument("--headless")  # Ensures the browser runs in headless mode
    chrome_options.add_argument('window-size=1920x1080')
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    url = "https://ledextract.ces.census.gov/qwi/all"

    qwi_files = [file for file in os.listdir("./Upload") if file.endswith(".qwi")]
    for file in tqdm(qwi_files, desc="Downloading QWI Data"):
        fullpath = os.path.abspath(f'./Upload/{file}')
        print(f"Processing {file}")
        driver.get(url)
        time.sleep(1)

        link = driver.find_elements(By.ID, "show_load_settings")
        link[0].click(); time.sleep(0.25)

        file_input = driver.find_elements(By.ID, "load_settings_input")
        file_input[0].send_keys(fullpath)

        submit = driver.find_elements(By.ID, "load_settings")
        submit[0].click(); time.sleep(1)

        worker_characteristics_tab = driver.find_element(By.ID, "tabs_tablist_worker_char_tab")
        worker_characteristics_tab.click()
        time.sleep(0.25)
        sex_education_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@type='radio'][@name='worker_xing'][@value='se']")))
        sex_education_button.click()
        time.sleep(0.25)
        edu_buttons = [
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            for xpath in [
                "//input[@type='checkbox'][@name='worker_se_education'][@value='E0']",
            ]
        ]
        for btn in edu_buttons: btn.click()
        time.sleep(0.25)
        export_tab = driver.find_elements(By.ID, "tabs_tablist_export_tab")
        export_tab[0].click(); time.sleep(0.25)

        time.sleep(1)
        submit_request_button = driver.find_elements(By.XPATH, "//b[text()='Submit Request']")
        submit_request_button[0].click(); time.sleep(25)

        download_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "CSV")))
        download_link.click()
        time.sleep(25)

        export_request_element = wait.until(EC.presence_of_element_located((By.ID, "export_request_id")))
        export_request_id = export_request_element.text

        if file.startswith('USA_DATA'):
            os.rename(f'./QWI_Data/qwi_{export_request_id}.csv', f'./QWI_Data/QWI_USA.csv')
        else:
            year = str(file[-8:-4])
            os.rename(f'./QWI_Data/qwi_{export_request_id}.csv', f'./QWI_Data/QWI_{year}.csv')
    
        time.sleep(5)
    driver.quit()

############################################################################################################
    
def getPopData():
    # Download population data
    url = 'https://www2.census.gov/programs-surveys/popest/datasets/2020-2022/metro/totals/cbsa-est2022.csv'
    popDF = pd.read_csv(url, encoding='latin-1', low_memory=False)
    popDF.rename(columns={'CBSA': 'CBSACode', 'NAME': 'geography_label.value'}, inplace=True)
    popDF = popDF[(popDF['LSAD'] == 'Metropolitan Statistical Area') | (popDF['LSAD'] == 'Micropolitan Statistical Area')]
    popDF = popDF[['CBSACode', 'POPESTIMATE2022', 'LSAD']]
    return popDF

def categorize_population(pop):
    if pop < 500000:
        return 'SMALL'
    elif 500000 <= pop <= 999999:
        return 'MEDIUM'
    else:
        return 'LARGE'

def getMetroSize(df, popDF):
    # Ensure CBSACode is string in both DataFrames
    df['CBSACode'] = df['CBSACode'].astype(str)
    popDF['CBSACode'] = popDF['CBSACode'].astype(str)
    # Merge DataFrames
    merged_df = pd.merge(df, popDF, on='CBSACode')
    merged_df['MetroSize'] = merged_df['POPESTIMATE2022'].apply(categorize_population)
    merged_df = merged_df[merged_df['LSAD'] != 'Micropolitan Statistical Area']
    merged_df.drop(columns=['POPESTIMATE2022', 'LSAD'], inplace=True)
    return merged_df

def get_trends(filename, type):
        df = pd.read_csv(filename)
        # Step 1: Creating 'firmage' column and dropping 'firmage_label.value'
        firmage_map = {
            "0-1 Years": "_0_1_years",
            "2-3 Years": "_2_3_years",
            "4-5 Years": "_4_5_years",
            "All Firm Ages": "_all_years"
        }
        education_map = {
            "Less than high school": "_less_high",
            "High school or equivalent, no college": "_high_school",
            "Some college or Associate degree": "_associate",
            "Bachelor's degree or advanced degree": "_bachelors"
            }
        df['firmage'] = df['firmage_label.value'].map(firmage_map)
        
        if type == 'YF':
            df.drop(['firmage_label.value', 'geography'], axis=1, inplace=True)
            df_wide = df.pivot_table(index=['year', 'quarter'], columns='firmage', values='Emp', aggfunc='first')
            # Calculate EMP_youngfirm
            df_wide['EMP_youngfirm'] = df_wide[['_0_1_years', '_2_3_years', '_4_5_years']].sum(axis=1)
            # Calculate YF_emp_share
            df_wide['YF_emp_share'] = df_wide['EMP_youngfirm'] / df_wide['_all_years']
            # Drop unnecessary columns
            df_wide.drop(['_0_1_years', '_2_3_years', '_4_5_years', 'EMP_youngfirm', '_all_years'], axis=1, inplace=True)
            # Collapse to get the mean of YF_emp_share by year
            df_collapsed = df_wide.groupby('year')['YF_emp_share'].mean().reset_index()
            # Set year as a time series index
            df_collapsed.set_index('year', inplace=True)
            # Generate lagged_emp_share
            df_collapsed['lagged_emp_share'] = df_collapsed['YF_emp_share'].shift(1)
            # Calculate YoY growth
            df_collapsed['trend'] = (df_collapsed['YF_emp_share'] - df_collapsed['lagged_emp_share']) / df_collapsed['lagged_emp_share'] 
            return df_collapsed
        elif type == 'YF_KI':
            df['edu_level'] = df['education_label.value'].map(education_map)
            df = df[df['education_label.value'] != "All Education Categories"]
            # Create 'firmage' column
            df.drop(['education_label.value', 'firmage_label.value', 'geography'], axis=1, inplace=True)
            # Filter out '_all_years' from 'firmage'
            df = df[df['firmage'] != '_all_years']
            # Reshape the data from long to wide format
            df_wide = df.pivot_table(index=['year', 'quarter', 'firmage'], columns='edu_level', values='Emp', aggfunc='first')
            # Sum the employment by education level
            df_wide['Emp_all'] = df_wide.sum(axis=1)
            # Calculate knowledge_intensity_ratio
            df_wide['knowledge_intensity_ratio'] = df_wide['_bachelors'] / df_wide['Emp_all']
            # Collapse to get the mean of knowledge_intensity_ratio by year
            df_collapsed = df_wide.groupby('year')['knowledge_intensity_ratio'].mean().reset_index()
            # Set year as a time series index
            df_collapsed.set_index('year', inplace=True)
            # Generate lagged_intensity_ratio
            df_collapsed['lagged_intensity_ratio'] = df_collapsed['knowledge_intensity_ratio'].shift(1)
            # Calculate YoY growth
            df_collapsed['trend'] = (df_collapsed['knowledge_intensity_ratio'] - df_collapsed['lagged_intensity_ratio']) / df_collapsed['lagged_intensity_ratio']

            return df_collapsed

def apply_trends(df, trend_df, type):
    # Check if 'year' is already the index; if not, set it
    if 'year' not in trend_df.columns and 'year' not in trend_df.index.names:
        raise ValueError("trend_df does not have a 'year' column or index")

    if 'year' in trend_df.columns:
        trend_df.set_index('year', inplace=True)

    most_recent_trend_year = trend_df.index.max()

    for index, row in df.iterrows():
        if row['MetroSize'] != 'SMALL':
            start_year = int(row['year'])
            end_year = int(min(most_recent_trend_year, df['year'].max()))
            if type == 'YF':
                current_emp = row['YF_Emp_Share']
                for year in range(start_year, end_year + 1):
                    if year in trend_df.index:
                        trend = trend_df.loc[year, 'trend']
                        current_emp *= (1 + trend)
                        df.at[index, 'YF_Emp_Share'] = int(current_emp)  # Convert to integer
                        df.at[index, 'year'] = most_recent_trend_year
            elif type == 'YF_KI':
                current_emp = row['YF_K_INT']
                for year in range(start_year, end_year + 1):
                    if year in trend_df.index:
                        trend = trend_df.loc[year, 'trend']
                        current_emp *= (1 + trend)
                        df.at[index, 'YF_K_INT'] = int(current_emp)  # Convert to integer
                        df.at[index, 'year'] = most_recent_trend_year

    return df

def transform_data(df, calc_type):
    firmage_map = {
        "0-1 Years": "Emp_0_1_years",
        "2-3 Years": "Emp_2_3_years",
        "4-5 Years": "Emp_4_5_years",
        "All Firm Ages": "Emp_all_years"
    }
    education_map = {
    "Less than high school": "_less_high",
    "High school or equivalent, no college": "_high_school",
    "Some college or Associate degree": "_associate",
    "Bachelor's degree or advanced degree": "_bachelors"
    }
    df['firmage'] = df['firmage_label.value'].map(firmage_map)
    df.drop('firmage_label.value', axis=1, inplace=True)
    if calc_type == 'YF':
        df_wide = df.pivot_table(index=['year', 'quarter', 'MetroSize', 'CBSACode'], 
                                    columns='firmage', 
                                    values='Emp', 
                                    aggfunc='sum', 
                                    fill_value=0).reset_index()
        df_agg = df_wide.groupby(['CBSACode', 'year', 'MetroSize']).agg({
            'Emp_0_1_years': 'sum', 
            'Emp_2_3_years': 'sum', 
            'Emp_4_5_years': 'sum', 
            'Emp_all_years': 'sum'
        }).reset_index()
        df_agg['emp_0_5_years'] = df_agg[['Emp_0_1_years', 'Emp_2_3_years', 'Emp_4_5_years']].sum(axis=1)
        df_agg['emp_qrt_ratio'] = df_agg['emp_0_5_years'] / df_agg['Emp_all_years']
        final_df = df_agg.groupby(['CBSACode', 'year', 'MetroSize'])['emp_qrt_ratio'].mean().reset_index()
        final_df['YF_Emp_Share'] = final_df['emp_qrt_ratio'] * 100
        final_df.drop('emp_qrt_ratio', axis=1, inplace=True)

    elif calc_type == 'YFKI':
        df = df[df['firmage'] != 'All Firm Ages']
        df['education'] = df['education_label.value'].map(education_map)
        df.drop('education_label.value', axis=1, inplace=True)
        df_wide = df.pivot_table(index=['quarter', 'CBSACode', 'firmage', 'year', 'MetroSize'], 
                                    columns='education', 
                                    values='Emp', 
                                    aggfunc='sum', 
                                    fill_value=0).reset_index()
        df_agg = df_wide.groupby(['CBSACode', 'quarter', 'year', 'MetroSize']).agg({
            '_associate': 'sum', 
            '_bachelors': 'sum', 
            '_high_school': 'sum', 
            '_less_high': 'sum'
        }).reset_index()
        df_agg['Emp_edu_1_4'] = df_agg[['_associate', '_bachelors', '_high_school', '_less_high']].sum(axis=1)
        df_agg['int_qrt_ratio'] = df_agg['_bachelors'] / df_agg['Emp_edu_1_4']
        final_df = df_agg.groupby(['CBSACode', 'year', 'MetroSize'])['int_qrt_ratio'].mean().reset_index()
        final_df['YF_K_INT'] = final_df['int_qrt_ratio'] * 100
        final_df.drop('int_qrt_ratio', axis=1, inplace=True)
    return final_df

def yf_emp():
    print('Calculating Young Firm Employment Share')
    qwi_files = [file for file in os.listdir("./QWI_Data") if file.endswith(".csv") and "YF" not in file]
    popDF = getPopData()
    dfs = []
    trend_df = get_trends('./QWI_Data/QWI_USA.csv', 'YF')
    for file in tqdm(qwi_files, desc="Transforming QWI Data"):
        fullpath = os.path.abspath(f'./QWI_Data/{file}')
        if file.startswith('QWI_USA') or file.startswith('QWI_AllStates') or file.startswith('USA'):
            continue        
        df = pd.read_csv(fullpath, index_col=False, low_memory=False, 
                         usecols=['geography_label.value','geography', 'education_label.value', 'firmage_label.value', 'quarter', 'year', 'Emp'])
        df['CBSACode'] = df['geography'].astype(str).str[-5:]
        df.drop('geography', axis=1, inplace=True)
        dfs.append(df)

    final_df = pd.concat(dfs)
    final_df = getMetroSize(final_df, popDF)
    final_df = transform_data(final_df, 'YF')
    final_df = apply_trends(final_df, trend_df, 'YF')
    final_df['zscore'] = (final_df['YF_Emp_Share'] - final_df['YF_Emp_Share'].mean()) / final_df['YF_Emp_Share'].std()
    final_df.drop('year', axis=1, inplace=True)
    os.makedirs("./Output", exist_ok=True)
    final_df.to_csv('./Output/YoungFirmEmploymentShare.csv', index=False)

def yfki():
    print('Calculating Young Firm Knowledge Intensity')
    qwi_files = [file for file in os.listdir("./QWI_Data") if file.endswith(".csv") and "YF" not in file]
    popDF = getPopData()
    dfs = []
    trend_df = get_trends('./QWI_Data/QWI_USA.csv', 'YF_KI')
    for file in tqdm(qwi_files, desc="Transforming QWI Data"):
        fullpath = os.path.abspath(f'./QWI_Data/{file}')
        if file.startswith('QWI_USA') or file.startswith('QWI_AllStates') or file.startswith('USA'):
            continue        
        df = pd.read_csv(fullpath, index_col=False, low_memory=False, 
                         usecols=['geography_label.value','geography', 'education_label.value', 'firmage_label.value', 'quarter', 'year', 'Emp'])
        df['CBSACode'] = df['geography'].astype(str).str[-5:]
        df.drop('geography', axis=1, inplace=True)
        dfs.append(df)

    final_df = pd.concat(dfs)
    final_df = getMetroSize(final_df, popDF)
    final_df = transform_data(final_df, 'YFKI')
    final_df = apply_trends(final_df, trend_df, 'YF_KI')
    final_df['zscore'] = (final_df['YF_K_INT'] - final_df['YF_K_INT'].mean()) / final_df['YF_K_INT'].std()
    final_df.drop('year', axis=1, inplace=True)
    os.makedirs("./Output", exist_ok=True)
    final_df.to_csv('./Output/YoungFirmKnowledgeIntensity.csv', index=False)


if __name__ == "__main__":
    start_time = time.time()
    print('Scraping QWI Data')
    # os.makedirs("./QWI_Data", exist_ok=True)
    # metro_year = scrape_years_and_metros()
    # if os.path.exists('./TempUpload'):
    #     shutil.rmtree('./TempUpload')

    # download_file()
    yf_emp()
    yfki()
    # end_time = time.time()
    # time_elapsed = end_time - start_time
    # minutes = int(time_elapsed // 60)
    # seconds = int(time_elapsed % 60)

    # # Print formatted time
    # print(f"Runtime: {minutes}:{seconds:02d}")
     
