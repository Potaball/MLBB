import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from typing import Literal
import ast
import math
import Levenshtein
from datetime import datetime
import re


# Params
my_hero = "Xborg"
markersize_1 = 5
markersize_2 = 5
linewidth_1 = 0.5
linewidth_2 = 2


# Autocorrect function
def correcting(x, my_correct_list):
    # Initialize variables to keep track of the best match
    closest_match = None
    min_distance = float('inf')
    for word in my_correct_list:
        # Compute the Levenshtein distance between the input word and each word in the list
        distance = Levenshtein.distance(x, word)
        # If the computed distance is smaller than the smallest found so far, update the closest match
        if distance < min_distance:
            min_distance = distance
            closest_match = word
    return closest_match

# Function to extract the date part and the rest of the filename
def extract_date_and_suffix(filename):
    # Remove the ".xlsx" suffix and keep the rest
    base_name = filename.replace('.xlsx', '')
    # Use regex to match the date part and the suffix (anything after the date)
    match = re.match(r"(\D+)(\d{4}) (\d{1,2}) (\d{1,2})(.*)", base_name)
    if match:
        # Extract the year, month, and day parts
        year = int(match.group(2))
        month = int(match.group(3))
        day = int(match.group(4))
        # Extract the rest of the string (anything after the date)
        suffix = match.group(5).strip().lower()  # Convert to lowercase for consistent sorting
    else:
        year = month = day = None
        suffix = base_name.lower()
    # Create a datetime object for accurate sorting
    date_obj = datetime(year, month, day) if year and month and day else None
    # Return a tuple (date_obj, suffix) to be used as the sorting key
    return (date_obj, suffix)

# Load the dfs
folder_path = 'Meta Result'
subfolder_path_list = ['ALL', 'Epic', 'Legend', 'Mythic', 'Mythical Honor', 'Mythical Glory+']
total_df_list = []
for subfolder_path in subfolder_path_list:
    file_list = [f for f in os.listdir(folder_path + '/' + subfolder_path) if "~" not in f and f.endswith('.xlsx') or f.endswith('.xls')]
    # Sort the list of filenames based on the extracted date and suffix
    file_list = sorted(file_list, key=extract_date_and_suffix)
    df_list = []
    for file in file_list:
        file_path = os.path.join(folder_path, subfolder_path, file)
        df = pd.read_excel(file_path)
        df_list.append(df)
    total_df_list.append(df_list)


# Check if hero name is correct
hero_list = total_df_list[-1][-1]['Hero'][total_df_list[-1][-1]['Hero'].notna()].tolist()
if not my_hero in hero_list:
    incorrect_my_hero = my_hero
    my_hero = correcting(my_hero, hero_list)
    print(f'Your input hero "{incorrect_my_hero}" is correct to "{my_hero}"\n')


# Extract pickrate, winrate and banrate
total_pickrate_list = [[] for _ in range(len(subfolder_path_list))]
total_winrate_list = [[] for _ in range(len(subfolder_path_list))]
total_banrate_list = [[] for _ in range(len(subfolder_path_list))]
for index, df_list in enumerate(total_df_list):
    for df in df_list:
        pickrate = df[df['Hero'] == my_hero]['Pick Rate'].iloc[0]
        winrate = df[df['Hero'] == my_hero]['Win Rate'].iloc[0]
        banrate = df[df['Hero'] == my_hero]['Ban Rate'].iloc[0]
        total_pickrate_list[index].append(pickrate)
        total_winrate_list[index].append(winrate)
        total_banrate_list[index].append(banrate)


# Right shift function
def right_shift(data, data_list):
    max_length = max([len(data) for data in data_list])
    # Create a new array with NaNs
    shifted_data = np.full(max_length, np.nan)
    # Place the original data in the new array
    shift_amount = max_length - len(data) 
    data = [float(p.strip('%')) / 100 for p in data]
    shifted_data[shift_amount:] = data
    return shifted_data


# Visualize the data
fig, ax1 = plt.subplots(figsize=(10,8))
fig.subplots_adjust(right=0.75)
ax2 = ax1.twinx()
handles, labels = [], []
colors = ['red', 'orange', 'green', 'blue', 'purple', 'black']
for i, pickrate_list in enumerate(total_pickrate_list):
    shifted_pickrate = right_shift(pickrate_list, total_pickrate_list)
    if i < 5:
        handle, = ax1.plot(shifted_pickrate, label=f'Pickrate Series {i+1}', color=colors[i % len(colors)], marker='o', linewidth=linewidth_1, markersize=markersize_1)
    else:
        handle, = ax1.plot(shifted_pickrate, label=f'Pickrate Series {i+1}', color=colors[i % len(colors)], marker='o', linewidth=linewidth_2, markersize=markersize_2)
    handles.append(handle)
    labels.append(f'Pickrate Series {i+1}')
for i, banrate_list in enumerate(total_banrate_list):
    shifted_banrate = right_shift(banrate_list, total_banrate_list)
    if i < 5:
        handle, = ax1.plot(shifted_banrate, label=f'Banrate Series {i+1}', color=colors[i % len(colors)], marker='s', linewidth=linewidth_1, markersize=markersize_1)
    else:
        handle, = ax1.plot(shifted_banrate, label=f'Banrate Series {i+1}', color=colors[i % len(colors)], marker='s', linewidth=linewidth_2, markersize=markersize_2)
    handles.append(handle)
    labels.append(f'Banrate Series {i+1}')
for i, winrate_list in enumerate(total_winrate_list):
    shifted_winrate = right_shift(winrate_list, total_winrate_list)
    if i < 5:
        handle, = ax2.plot(shifted_winrate, label=f'Winrate Series {i+1}', color=colors[i % len(colors)], marker='x', linewidth=linewidth_1, markersize=markersize_1)
    else:
        handle, = ax2.plot(shifted_winrate, label=f'Winrate Series {i+1}', color=colors[i % len(colors)], marker='x', linewidth=linewidth_2, markersize=markersize_2)
    handles.append(handle)
    labels.append(f'Winrate Series {i+1}')
ax1.set_yscale('log')
ax1.legend(handles, labels, loc='upper left', bbox_to_anchor=(1.1, 1))
xticks = ax1.get_xticks()
xtick_labels = [str(int(label)) for label in xticks]
inverted_labels = xtick_labels[::-1]
ax1.xaxis.set_major_locator(plt.FixedLocator(xticks))
ax1.xaxis.set_major_formatter(plt.FixedFormatter(inverted_labels))
ax1.set_ylabel('Pickrate / Banrate')
ax2.set_ylabel('Winrate')
ax1.set_xlabel('Past days')
ax1.set_title(f'Basic data of {my_hero}')
ax1.set_yticks([0.0001, 0.001, 0.01, 0.1, 1, 10])
ax2.set_yticks([0.3, 0.4, 0.5, 0.6, 0.7])
plt.show()