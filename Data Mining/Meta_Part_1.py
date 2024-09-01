# Ths method extract data directly from the mobile legend website
# Then process the data and calculate the metability
# Then output the result as xlsx file

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random
import pandas as pd
from datetime import datetime
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import pyautogui
from tqdm import tqdm
import threading
import pickle

rank_list = ['ALL', 'Epic', 'Legend']

# Get current date
today = datetime.today()

def open_browser():
    # Set Edge options for headless mode
    edge_options = Options()
    edge_options.add_argument("--headless")  # Comment this line if you want to see the browser window
    edge_options.add_argument("--window-size=1920x1080")
    edge_options.add_argument('--disable-notifications')

    # Set the URL of the website you want to scrape
    url = 'https://m.mobilelegends.com/rank'
    driver = webdriver.Edge(options=edge_options)
    driver.command_executor.set_timeout(10)
    driver.get(url)
    return driver

# Set up the wait time
wait_time = (2,4,2)
def waiting(my_min, my_max, my_mode):
    return random.triangular(my_min, my_max, my_mode)

def get_meta():
    driver = open_browser()
    # Get the size of the browser window and the center coordinates
    window_size = driver.get_window_size()
    center_x = window_size['width'] / 3
    center_y = window_size['height'] / 3
    
    time.sleep(waiting(*wait_time))
    # Wait for privacy update pop up if it exists
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='mt-cb-policy-title' and text()='Privacy Policy Update']")))
    except TimeoutException:
        pass

    # If privacy update window exist, close it
    try:
        clickable = driver.find_element(By.CSS_SELECTOR, 'div.mt-cb-policy-close')
        actions = ActionChains(driver)
        actions.click(clickable).perform()
    except Exception as e:
        print(e)

    # Wait for the page to load then
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), 'ALL')]")))
    except TimeoutException:
        print('Timed out waiting for page to load.')
        driver.quit()
        return None

    # Click to expand the rank dropdown list
    clickable = driver.find_element(By.CSS_SELECTOR, 'div.mt-2684886.mt-text[data-node="2684886"]')
    actions = ActionChains(driver)
    actions.click(clickable).perform()

    # Then click on the desired rank according to rank_list defined above
    time.sleep(waiting(*wait_time))
    try:
        clickable = driver.find_elements(By.XPATH, f"//span[contains(text(), '{rank}')]")[0]
        actions = ActionChains(driver)
        actions.click(clickable).perform()
        rank_existance = True
    except:
        raise Exception(f"{rank} Rank doesn't exist yet, try another day")
        rank_existance = False

    if rank_existance:
        # Wait for the page to load
        not_clicked = True
        for i in range(10):
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > *:last-child')))
            except TimeoutException:
                print('Timed out waiting for page to load.')
                driver.quit()
                return None
            
            # Click the website once
            if not_clicked:
                # Click to expand the rank dropdown list
                clickable = driver.find_element(By.CSS_SELECTOR, 'div.mt-2684827.mt-empty[data-node="2684827"]')
                action = ActionChains(driver)
                action.click(clickable).perform()
                not_clicked = False

            # Simulate pressing the DOWN arrow key 20 times
            for _ in range(100):
                action.send_keys(Keys.ARROW_DOWN)
                time.sleep(0.01)
                #time.sleep(random.random()/100)  # Adjust sleep time as needed
            
            # Perform all the actions
            action.perform()
            time.sleep(waiting(*wait_time))


        # Find all the listings on the current page
        listings = driver.find_elements(By.CSS_SELECTOR, 'div.mt-2684910.mt-list-layout.scroll-y[data-node="2684910"]')
        if len(listings) == 0:
            return None
        data_string = listings[0].text
        data_points = data_string.split('\n')

        # Iterate over the data points, assuming each entry has a fixed number of fields
        data = []
        for i in range(0, len(data_points), 5):
            if i + 4 < len(data_points):  # Ensure there are enough elements left
                entry = {
                    "Hero": data_points[i + 1],
                    "Pick Rate": data_points[i + 2],
                    "Win Rate": data_points[i + 3],
                    "Ban Rate": data_points[i + 4]
                }
                data.append(entry)

        # Convert to df
        df = pd.DataFrame(data)
        # Function to clean and convert a single value
        def convert_percentage_to_decimal(percentage_str):
            # Remove the percentage sign
            if percentage_str.endswith('%'):
                percentage_str = percentage_str[:-1]
            # Convert to float and divide by 100
            return float(percentage_str) / 100
        # Apply the function to the 'Amount' column
        df['_Pick Rate'] = df['Pick Rate'].apply(convert_percentage_to_decimal)
        df['_Win Rate'] = df['Win Rate'].apply(convert_percentage_to_decimal)
        df['_Ban Rate'] = df['Ban Rate'].apply(convert_percentage_to_decimal)
        df['_Ban Rate'] = df['_Ban Rate'].clip(lower=0, upper=0.999)
        df['Metability'] = (df['_Win Rate'] - 0.5) * df['_Pick Rate'] * (1/(1 - df['_Ban Rate'])) * 10000
        df = df.drop(columns=['_Pick Rate', '_Win Rate', '_Ban Rate'], axis=1)
        df = df.sort_values(by='Metability', ascending=False)
        df.reset_index(drop=True, inplace=True)
        driver.close()
        return df
    driver.close()
    return None

for rank in tqdm(rank_list, desc='Rank Level'):
    # Save to excel
    df = get_meta()
    threshold = 123
    if df is not None and len(df) > 0:
        is_export_df = True
        while df.shape[0] < threshold:
            time.sleep(5)
            df = get_meta()
            if df is None or len(df) == 0:
                is_export_df = False
                break
            elif df.shape[0] >= threshold:
                is_export_df = True
        if is_export_df:
            df.to_excel(f'Meta Result/{rank}/Meta Result {rank} {today.year} {today.month} {today.day}.xlsx')
