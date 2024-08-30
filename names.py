import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

def setup_driver():
    chrome_options = Options()
    #chrome_options.add_argument("--headless")  # Run headless if needed
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def navigate_to_progress_monitoring(driver):
    # Navigate to the main URL
    url = 'https://omms.nic.in/'
    driver.get(url)
    
    # Wait for the dropdown to be clickable and click it using XPath
    print("Waiting for progress monitoring dropdown...")
    progress_monitoring = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="divMenuBar"]/div/div/ul/li[4]/a'))
    )
    print("Progress monitoring dropdown found. Clicking...")
    progress_monitoring.click()
    
    # Wait for the dropdown menu item to be clickable and click it using XPath
    print("Waiting for road wise progress menu item...")
    road_wise_progress = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="divMenuBar"]/div/div/ul/li[4]/ul/div/li[1]/ul/li[7]/a'))
    )
    print("Road wise progress menu item found. Clicking...")
    road_wise_progress.click()

def get_blocks_for_states(driver, state_names):
    data = []

    # Navigate to the progress monitoring section only once
    navigate_to_progress_monitoring(driver)
    
    for state_name in state_names:
        # Wait for the state dropdown to be visible and select the given state
        print("Waiting for state dropdown")
        state_dropdown = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="StateList_RoadWiseProgressDetails"]'))
        )
        print(f"State dropdown found. Selecting {state_name}...")
        select_state = Select(state_dropdown)
        select_state.select_by_visible_text(state_name)

        # Wait for the year dropdown to be visible and select "2008-2009"
        print("Waiting for year dropdown...")
        year_dropdown = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="YearList_RoadWiseProgressDetails"]'))
        )
        print("Year dropdown found. Selecting 2008-2009...")
        select_year = Select(year_dropdown)
        select_year.select_by_visible_text('2008-2009')

        # Wait for the scheme dropdown to be visible and select "PMGSY1"
        print("Waiting for scheme dropdown...")
        scheme_dropdown = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="SchemeList_RoadWiseProgressDetails"]'))
        )
        print("Scheme dropdown found. Selecting PMGSY1...")
        select_scheme = Select(scheme_dropdown)
        select_scheme.select_by_visible_text('PMGSY1')

        # Adding a delay to ensure the district dropdown is populated
        time.sleep(3)

        # Wait for the district dropdown to be visible
        print("Waiting for district dropdown...")
        district_dropdown = WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, '//*[@id="DistrictList_RoadWiseProgressDetails"]'))
        )
        print("District dropdown found.")
        select_district = Select(district_dropdown)
        district_options = select_district.options

        for district_option in district_options:
            district_value = district_option.get_attribute('value')
            if district_value != '0':  # Skip "All Districts" option
                print(f"Selecting district: {district_option.text}")
                select_district.select_by_value(district_value)
                
                # Adding a delay to ensure the block dropdown is populated
                time.sleep(3)

                # Wait for the block dropdown to be visible
                print("Waiting for block dropdown...")
                block_dropdown = WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@id="BlockList_RoadWiseProgressDetails"]'))
                )
                print("Block dropdown found.")
                select_block = Select(block_dropdown)
                block_options = select_block.options

                # Collect block data
                if len(block_options) == 1 and block_options[0].get_attribute('value') == '0':
                    print(f"Recording block: {block_options[0].text} for district {district_option.text}")
                    data.append([state_name, district_option.text, block_options[0].text])
                else:
                    for block_option in block_options:
                        block_value = block_option.get_attribute('value')
                        if block_value != '0':  # Skip "All Blocks" if there are more options
                            print(f"Recording block: {block_option.text} for district {district_option.text}")
                            data.append([state_name, district_option.text, block_option.text])

    return data

def save_to_csv(data, filename='names.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["State", "District", "Block"])
        writer.writerows(data)

def main():
    states = ["Andhra Pradesh", "Bihar", "Haryana", "Maharashtra", "Rajasthan"]
    driver = setup_driver()
    try:
        data = get_blocks_for_states(driver, states)
        save_to_csv(data)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
