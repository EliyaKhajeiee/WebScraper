import csv
import re
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Set up WebDriver with options
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Optional: Run Chrome in headless mode
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def random_sleep(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

def login_to_keystone(driver):
    driver.get('https://preview.orderkeystone.com/crash')
    random_sleep()
    
    # Step 1: Enter User ID and submit
    try:
        # Wait for the user ID field to be visible
        user_id_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, 'username'))
        )
        # Wait for the submit username button to be clickable
        submit_username_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit Username']"))
        )
        
        user_id_field.send_keys('abraham.khajeie')  # Replace with your actual User ID
        submit_username_button.click()
        print("User ID submitted successfully.")
        random_sleep(3)
    except TimeoutException:
        print("Timed out waiting for User ID field or submit button to be available.")
        return
    
    # Step 2: Enter Password and submit
    try:
        # Wait for the password field to be visible
        password_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, 'passwordTextBox'))
        )
        
        # Enter password
        password_field.send_keys('Eagle123#')  # Replace with your actual Password
        
        # Wait until the login button is clickable
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']"))
        )
        login_button.click()
        print("Password submitted successfully and login button clicked.")
        random_sleep(3)  # Wait for login to complete
    except TimeoutException:
        print("Timed out waiting for password field or login button to be available.")
# Login to Keystone
login_to_keystone(driver)

quit()
# Prepare CSV files for writing extracted data
with open('part_titles.csv', 'w', newline='') as titles_csv, \
     open('part_details.csv', 'w', newline='') as details_csv, \
     open('fitments_data.csv', 'w', newline='') as fitments_csv:

    # CSV writers
    titles_writer = csv.writer(titles_csv)
    details_writer = csv.writer(details_csv)
    fitments_writer = csv.writer(fitments_csv)

    # Write headers
    titles_writer.writerow(['PartLinkNumber', 'TITLE'])
    details_writer.writerow(['PartLinkNumber', 'KEY', 'Data'])
    fitments_writer.writerow(['PartLinkNumber', 'Make', 'Model', 'Years'])

    # Read part numbers from a text file
    file_path = 'C:\\Users\\Abraham\\Desktop\\part_numbers.txt'
    with open(file_path, 'r') as file:
        part_numbers = [line.strip() for line in file.readlines()]

    for part_number in part_numbers:
        try:
            driver.get('https://preview.orderkeystone.com/crash')
            random_sleep()

            # Search for part number
            search_field = driver.find_element(By.NAME, 'search')
            search_field.send_keys(part_number)
            search_field.send_keys(Keys.RETURN)
            random_sleep()

            # Click on the part image
            part_image = driver.find_element(By.CSS_SELECTOR, '.part-card-image')
            part_image.click()
            random_sleep()

            # PART 1: Extract the bolded title (description)
            try:
                title_element = driver.find_element(By.CSS_SELECTOR, '.product-title')
                title = title_element.text
                titles_writer.writerow([part_number, title])
            except Exception as e:
                print(f"Failed to extract title for part number {part_number}: {str(e)}")

            # PART 2: Extract OEM / ALT Numbers and sub-descriptions as KEY-DATA pairs
            try:
                # Extract OEM / ALT Numbers
                oem_alt_numbers = driver.find_elements(By.CSS_SELECTOR, '.mat-tab-body-content .modal-detail-content')
                for element in oem_alt_numbers:
                    data = element.text
                    if '-' not in data and data != part_number:
                        details_writer.writerow([part_number, 'OEM', data])

                # Extract sub-descriptions
                sub_descriptions = driver.find_element(By.CSS_SELECTOR, '.part-description').text
                sub_descriptions_list = re.findall(r'•\s*(.+)', sub_descriptions)
                for desc in sub_descriptions_list:
                    details_writer.writerow([part_number, 'Property', desc])
            except Exception as e:
                print(f"Failed to extract details for part number {part_number}: {str(e)}")

            # PART 3: Extract and process Fitments data
            try:
                fitments_data = driver.find_element(By.CSS_SELECTOR, '.mat-grid-list').text
                fitments_lines = fitments_data.split("\n")

                # Parse Fitments data
                fitments_parsed = []
                for line in fitments_lines:
                    match = re.match(r'(\d{4})\s+(\w+)\s+(\w+)', line)
                    if match:
                        year, make, model = match.groups()
                        fitments_parsed.append((make, model, int(year)))

                # Create a dictionary to merge Make, Model, and Year ranges
                fitments_merged = {}
                for make, model, year in fitments_parsed:
                    key = f"{make}_{model}"
                    if key not in fitments_merged:
                        fitments_merged[key] = {'make': make, 'model': model, 'min_year': year, 'max_year': year}
                    else:
                        fitments_merged[key]['min_year'] = min(fitments_merged[key]['min_year'], year)
                        fitments_merged[key]['max_year'] = max(fitments_merged[key]['max_year'], year)

                # Write merged fitments data
                for key, data in fitments_merged.items():
                    fitments_writer.writerow([part_number, data['make'], data['model'], f"{data['min_year']}-{data['max_year']}"])
            except Exception as e:
                print(f"Failed to extract fitments for part number {part_number}: {str(e)}")

        except Exception as e:
            print(f"Failed to process part number {part_number}: {str(e)}")

driver.quit()
