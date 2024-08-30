#Automation Script
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-javascript")  # Disable JavaScript
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress console logs
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.javascript": 2})  # Another way to disable JavaScript
    return webdriver.Chrome(options=chrome_options)

def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def navigate_to_road_wise_progress(driver, max_retries=3):
    url = 'https://omms.nic.in/'
    for attempt in range(max_retries):
        try:
            driver.get(url)
            wait_for_page_load(driver)
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="divMenuBar"]/div/div/ul/li[4]/a'))
            ).click()
            wait_for_page_load(driver)
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="divMenuBar"]/div/div/ul/li[4]/ul/div/li[1]/ul/li[7]/a'))
            ).click()
            wait_for_page_load(driver)
            return True
        except (TimeoutException, NoSuchElementException) as e:
            if attempt == max_retries - 1:
                print(f"Failed to navigate to road wise progress page after {max_retries} attempts.")
                return False
            print(f"Navigation attempt {attempt + 1} failed. Retrying...")
            time.sleep(random.uniform(1, 3))

def select_dropdown(driver, xpath, value, max_retries=3):
    for attempt in range(max_retries):
        try:
            dropdown = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            select = Select(dropdown)
            select.select_by_visible_text(value)
            time.sleep(random.uniform(1, 2))
            return True
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
            if attempt == max_retries - 1:
                print(f"Failed to select '{value}' from dropdown after {max_retries} attempts.")
                return False
            print(f"Dropdown selection attempt {attempt + 1} failed. Retrying...")
            time.sleep(random.uniform(1, 3))

def get_data(driver, state, district, block, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Select dropdowns
            if not all([
                select_dropdown(driver, '//*[@id="StateList_RoadWiseProgressDetails"]', state),
                select_dropdown(driver, '//*[@id="YearList_RoadWiseProgressDetails"]', '2008-2009'),
                select_dropdown(driver, '//*[@id="SchemeList_RoadWiseProgressDetails"]', 'PMGSY1'),
                select_dropdown(driver, '//*[@id="DistrictList_RoadWiseProgressDetails"]', district),
                select_dropdown(driver, '//*[@id="BlockList_RoadWiseProgressDetails"]', block)
            ]):
                raise Exception("Failed to select all dropdowns")

            # Click view button
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="btnViewRoadWiseProgressWork"]'))
            ).click()

            wait_for_page_load(driver)

            # Switch to iframe
            iframe = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@id="loadReport"]/iframe'))
            )
            driver.switch_to.frame(iframe)

            # Get data from table
            xpath = '//table[.//div[text()="Block Name"]]' if block != 'All Blocks' else '//table[.//div[text()="District Name"]]'
            results_table = WebDriverWait(driver, 60).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )
            
            next_row = results_table.find_element(By.XPATH, f'.//tr[.//div[text()="{("Block" if block != "All Blocks" else "District")} Name"]]/following-sibling::tr[1]')
            row_data = [cell.text for cell in next_row.find_elements(By.XPATH, './/td')]

            # back to default content
            driver.switch_to.default_content()
            
            return row_data[2:5] if len(row_data) >= 5 else [""] * 3  
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error fetching data for State: {state}, District: {district}, Block: {block} - {e}")
                return [""] * 3  # Changed from 4 to 3
            print(f"Data fetching attempt {attempt + 1} failed. Retrying...")
            time.sleep(random.uniform(2, 5))

def process_rows(driver, rows, start_index, total_entries):
    results = []
    if not navigate_to_road_wise_progress(driver):
        return results

    for i, (_, row) in enumerate(rows, start=start_index):
        state, district, block = row['State'], row['District'], row['Block']
        print(f"[{i+1}/{total_entries}] Fetching data for State: {state}, District: {district}, Block: {block}")
        row_data = get_data(driver, state, district, block)
        results.append({
            'State': state,
            'District': district,
            'Block': block,
            'Total No. Of Works': row_data[0],
            'Road Length': row_data[1],
            'Sanction Cost': row_data[2]
            # 'Maintenance Cost' field removed
        })
    return results

def run(input_csv, output_csv, num_threads=4):
    df_input = pd.read_csv(input_csv)
    total_entries = len(df_input)
    data = []

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        chunk_size = (total_entries + num_threads - 1) // num_threads  # Ceiling division
        for i in range(0, total_entries, chunk_size):
            chunk = df_input.iloc[i:i+chunk_size].iterrows()
            driver = setup_driver()
            futures.append(executor.submit(process_rows, driver, chunk, i, total_entries))
        
        for future in as_completed(futures):
            data.extend(future.result())

    pd.DataFrame(data).to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")
    print(f"Total entries processed: {total_entries}")

if __name__ == "__main__":
    start_time = time.time()
    run('names.csv', 'final_output.csv', num_threads = 12)
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Total execution time: {total_time/60:.2f} minutes")