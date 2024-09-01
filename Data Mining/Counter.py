# Ths method extract data directly from the mobile legend website
# Then process the data and calculate the counter score and compati score
# Then output the result as xlsx file
# The whole script will run for about 30 minutes

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
from tqdm import tqdm
import pickle
import os
import traceback


# Set Edge options for headless mode
edge_options = Options()
edge_options.add_argument("--headless")  # Comment this line if you want to see the browser window
edge_options.add_argument("--window-size=1920x1080")

# Hero dictionary
hero_filename = 'Data Mining/id_hero_dict.pkl'
if os.path.isfile(hero_filename):
    with open(hero_filename, 'rb') as f:
        id_hero_dict = pickle.load(f)
else:
    id_hero_dict = {}     # key is hero id, value is hero name and image url
before_id_hero_dict_length = len(id_hero_dict)
counter_hero_dict = {}    # key is the weak hero being counter, value is strong hero id and counter score
compati_hero_dict = {}    # key is the best friend, value is their friends and friend score

# Set up the wait time
wait_time = (1,2,1)
def waiting(my_min, my_max, my_mode):
    return random.triangular(my_min, my_max, my_mode)

# Set the URL of the website you want to scrape
for hero_number in tqdm(range(1,130),desc='Hero ID', ncols=100):
    try:
        url = f'https://m.mobilelegends.com/hero/detail?channelid=2678756&heroid={hero_number}'
        driver = webdriver.Edge(options=edge_options)
        driver.get(url)

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

        # Wait for the page to load
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'COUNTERS')]")))
        except TimeoutException:
            print('Timed out waiting for page to load.')
            driver.quit()

        # Click into COUNTERS page
        #print('Click into COUNTERS page')
        clickable = driver.find_element(By.XPATH, "//span[contains(text(), 'COUNTERS')]")
        actions = ActionChains(driver)
        actions.click(clickable).perform()

        # Wait COUNTERS page to load
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.mt-2684329.mt-list[data-node="2684329"]')))
        except TimeoutException:
            print('Timed out waiting for page to load.')
            driver.quit()

        # Extract the hero image
        #print('Extract the hero image')
        hero_name = driver.find_element(By.CSS_SELECTOR, 'div.mt-2680124.mt-text[data-node="2680124"]').text
        hero_image = driver.find_element(By.CSS_SELECTOR, 'div.mt-2680184.mt-image[data-node="2680184"]').find_element(By.TAG_NAME, 'img').get_attribute('src')
        if hero_number not in id_hero_dict:
            id_hero_dict[hero_number] = [hero_name] 
            id_hero_dict[hero_number].append(hero_image)

        # Counter data (Best counters section)
        #print('Counter data (Best counters section)')
        counter_listings = driver.find_elements(By.CSS_SELECTOR, 'div.mt-2684329.mt-list[data-node="2684329"]')        
        # Iterate over the data points, assuming each entry has a fixed number of fields
        data_string = counter_listings[0].text
        data_points = data_string.split('\n')
        data = []
        for i in range(0, len(data_points), 2):
            if i + 1 < len(data_points):  # Ensure there are enough elements left
                data.append(float(data_points[i + 1]))
        # Extract the Counter score and assign them to the heroes
        for index, image in enumerate(counter_listings[0].find_elements(By.TAG_NAME, 'img')):
            image_source = image.get_attribute('src')
            if image_source in counter_hero_dict.keys():
                counter_hero_dict[image_source].append([hero_number, data[index]])
            else:
                counter_hero_dict[image_source] = [[hero_number, data[index]]]

        # Counter data (Most counter by section)
        #print('Counter data (Most counter by section)')
        clickable = driver.find_element(By.XPATH, "//span[contains(text(), 'Most Countered by')]")
        actions = ActionChains(driver)
        actions.click(clickable).perform()
        # Wait the Most Counter by sectiion to load
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.mt-2684508.mt-list[data-node="2684508"]')))
        except TimeoutException:
            print('Timed out waiting for page to load.')
            driver.quit()
        counter_listings = driver.find_elements(By.CSS_SELECTOR, 'div.mt-2684508.mt-list[data-node="2684508"]')        
        # Iterate over the data points, assuming each entry has a fixed number of fields
        data_string = counter_listings[0].text
        data_points = data_string.split('\n')
        data = []
        for i in range(0, len(data_points), 2):
            if i + 1 < len(data_points):  # Ensure there are enough elements left
                data.append(float(data_points[i + 1]))
        # Extract the Counter score and assign them to the heroes
        for index, image in enumerate(counter_listings[0].find_elements(By.TAG_NAME, 'img')):
            image_source = image.get_attribute('src')
            matching_number = [key for key, value in id_hero_dict.items() if value[1] == image_source][0]
            if hero_image in counter_hero_dict.keys():
                counter_hero_dict[hero_image].append([matching_number, -data[index]])
            else:
                counter_hero_dict[hero_image] = [[matching_number, -data[index]]]


        # Click the cookie to refuse it
        # If privacy update window exist, close it
        try:
            clickable = driver.find_element(By.CSS_SELECTOR, '#mt-cb-s.mt-cb-btn')
            actions = ActionChains(driver)
            actions.click(clickable).perform()
        except Exception as e:
            print(e)


        # Compati data (Compatible)
        #Wait for the page to load
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'mt-2684556') and contains(@class, 'mt-list') and @data-node='2684556']")))
        except TimeoutException:
            print('Timed out waiting for page to load.')
            driver.quit()
        #print('Compati data (Compatible)')
        compati_listings = driver.find_elements(By.CSS_SELECTOR, 'div.mt-2684556.mt-list[data-node="2684556"]')        
        # Iterate over the data points, assuming each entry has a fixed number of fields
        data_string = compati_listings[0].text
        data_points = data_string.split('\n')
        data = []
        for i in range(0, len(data_points), 2):
            if i + 1 < len(data_points):  # Ensure there are enough elements left
                data.append(float(data_points[i + 1]))
        # Extract the Compati score and assign them to the heroes and self
        for index, image in enumerate(compati_listings[0].find_elements(By.TAG_NAME, 'img')):
            image_source = image.get_attribute('src')
            # Assign to heroes
            if image_source in compati_hero_dict.keys():
                compati_hero_dict[image_source].append([hero_number, data[index]])
            else:
                compati_hero_dict[image_source] = [[hero_number, data[index]]]
            # Assign to self
            if id_hero_dict[hero_number][1] in compati_hero_dict.keys():
                compati_hero_dict[id_hero_dict[hero_number][1]].append([image_source, data[index]])
            else:
                compati_hero_dict[id_hero_dict[hero_number][1]] = [[image_source, data[index]]]

        # Compati data (Not Compatible)
        #print('Compati data (Not Compatible)')
        clickable = driver.find_element(By.XPATH, "//span[contains(text(), 'Not Compatible')]")
        actions = ActionChains(driver)
        actions.click(clickable).perform()
        # Wait Not Compatible section to load
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.mt-2684578.mt-list[data-node="2684578"]')))
        except TimeoutException:
            print('Timed out waiting for page to load.')
            driver.quit()
        compati_listings = driver.find_elements(By.CSS_SELECTOR, 'div.mt-2684578.mt-list[data-node="2684578"]')        
        # Iterate over the data points, assuming each entry has a fixed number of fields
        data_string = compati_listings[0].text
        data_points = data_string.split('\n')
        data = []
        for i in range(0, len(data_points), 2):
            if i + 1 < len(data_points):  # Ensure there are enough elements left
                data.append(float(data_points[i + 1]))
        # Extract the Compati score and assign them to the heroes and self
        for index, image in enumerate(compati_listings[0].find_elements(By.TAG_NAME, 'img')):
            image_source = image.get_attribute('src')
            # Assign to heroes
            if image_source in compati_hero_dict.keys():
                compati_hero_dict[image_source].append([hero_number, data[index]])
            else:
                compati_hero_dict[image_source] = [[hero_number, data[index]]]
            # Assign to self
            if id_hero_dict[hero_number][1] in compati_hero_dict.keys():
                compati_hero_dict[id_hero_dict[hero_number][1]].append([image_source, data[index]])
            else:
                compati_hero_dict[id_hero_dict[hero_number][1]] = [[image_source, data[index]]]


        # Close the web driver properly
        driver.quit()
        
    except Exception as e:
        print(e)
        traceback.print_exc()
        # Remove the error hero id
        if hero_number in id_hero_dict:
            id_hero_dict.pop(hero_number)

        # Close the web driver properly
        driver.quit()

# Convert the key from url to name in counter_hero_dict and compati_hero_dict
counter_hero_image_list = list(counter_hero_dict.keys())
id_hero_image_list = [i[1] for i in list(id_hero_dict.values())]
counter_hero_index = []
for index, image in enumerate(counter_hero_image_list):
    if image in id_hero_image_list:
        my_index = id_hero_image_list.index(image)
        counter_hero_dict[list(id_hero_dict.values())[my_index][0]] = counter_hero_dict[image]
        counter_hero_index.append(image)
for index in counter_hero_index:
    counter_hero_dict.pop(index)

compati_hero_image_list = list(compati_hero_dict.keys())
id_hero_image_list = [i[1] for i in list(id_hero_dict.values())]
compati_hero_index = []
for index, image in enumerate(compati_hero_image_list):
    if image in id_hero_image_list:
        my_index = id_hero_image_list.index(image)
        compati_hero_dict[list(id_hero_dict.values())[my_index][0]] = compati_hero_dict[image]
        compati_hero_index.append(image)
for index in compati_hero_index:
    compati_hero_dict.pop(index)

# Convert and sort the value from hero id to hero name in counter_hero_dict and compati_hero_dict
for key in counter_hero_dict.keys():
    new_data = []
    total_score = 0
    for counter_data in counter_hero_dict[key]:
        the_hero = id_hero_dict[counter_data[0]][0]
        if the_hero not in [nd[0] for nd in new_data]:
            new_data.append([the_hero, counter_data[1]])
            total_score += counter_data[1]
    new_data = sorted(new_data, key=lambda x: x[1], reverse=True)
    counter_hero_dict[key] = [total_score, new_data]

for key in compati_hero_dict.keys():
    new_data = []
    total_score = 0
    for compati_data in compati_hero_dict[key]:
        the_hero = id_hero_dict[counter_data[0]][0]
        if the_hero not in [nd[0] for nd in new_data]:
            try:
                new_data.append([the_hero, compati_data[1]])
            except:
                my_index = id_hero_image_list.index(compati_data[0])
                new_data.append([list(id_hero_dict.values())[my_index][0], compati_data[1]])
            total_score += compati_data[1]
    new_data = sorted([list(j) for j in list(set([tuple(i) for i in new_data]))], key=lambda x: x[1], reverse=True)
    compati_hero_dict[key] = [total_score, new_data]

# Add missing key into counter_hero_dict and compati_hero_dict
for hero, image in id_hero_dict.values():
    if hero not in counter_hero_dict.keys():
        counter_hero_dict[hero] = [0, []]

for hero, image in id_hero_dict.values():
    if hero not in compati_hero_dict.keys():
        compati_hero_dict[hero] = [0, []]

# Rank the counterality
counter_rank = []
for index, (tot, val) in enumerate(counter_hero_dict.values()):
    for v in val:
        counter_rank.append([*v, list(counter_hero_dict.keys())[index]])
counter_rank = sorted(counter_rank, key=lambda x: x[1], reverse=True)

# Rank the compatibility
compati_rank = []
for index, (tot, val) in enumerate(compati_hero_dict.values()):
    for v in val:
        compati_rank.append([*v, list(compati_hero_dict.keys())[index]])
compati_rank = sorted(compati_rank, key=lambda x: x[1], reverse=True)
new_compati_rank = []
for index, i in enumerate(compati_rank):
    if index < len(compati_rank) - 1:
        if i[0] != compati_rank[index+1][2] and i[2] != compati_rank[index+1][0]:
            new_compati_rank.append(i)
    else:
        new_compati_rank.append(i)
compati_rank = new_compati_rank
    

# Construct a dataframe for each dict
counter_df = pd.DataFrame(counter_hero_dict).transpose()
counter_df = counter_df.sort_values(by=0, ascending=False)
counter_df = counter_df.rename(columns={0:'Total weakness', 1:'Counter by'})

compati_df = pd.DataFrame(compati_hero_dict).transpose()
compati_df = compati_df.sort_values(by=0, ascending=False)
compati_df = compati_df.rename(columns={0:'Total friendship', 1:'Friend with'})

counter_rank_df = pd.DataFrame(counter_rank)
counter_rank_df = counter_rank_df.rename(columns={0:'Strong', 1:'Value', 2:'Weak'})

compati_rank_df = pd.DataFrame(compati_rank)
compati_rank_df = compati_rank_df.rename(columns={0:'Friend', 1:'Value', 2:'Friend'})

# Save the df as excel
today = datetime.today()
with pd.ExcelWriter(f'Counter Result/Counter Result {today.year} {today.month} {today.day}.xlsx', engine='xlsxwriter') as writer:
    # Write df1 to the first sheet starting at cell A1
    counter_rank_df.to_excel(writer, sheet_name='Sheet1', startrow=0, startcol=0, index=False)
    # Write df2 to the first sheet starting at cell C1 (two columns to the right of df1)
    counter_df.to_excel(writer, sheet_name='Sheet1', startrow=0, startcol=len(counter_rank_df.columns) + 1, index=True)

with pd.ExcelWriter(f'Compati Result/Compati Result {today.year} {today.month} {today.day}.xlsx', engine='xlsxwriter') as writer:
    # Write df1 to the first sheet starting at cell A1
    compati_rank_df.to_excel(writer, sheet_name='Sheet1', startrow=0, startcol=0, index=False)
    # Write df2 to the first sheet starting at cell C1 (two columns to the right of df1)
    compati_df.to_excel(writer, sheet_name='Sheet1', startrow=0, startcol=len(compati_rank_df.columns) + 1, index=True)

# Save the id_hero_dict
if len(id_hero_dict) > before_id_hero_dict_length:
    with open(hero_filename, 'wb') as f:
        pickle.dump(id_hero_dict, f)