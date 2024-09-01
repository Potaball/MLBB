import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from typing import Literal
import re
from datetime import datetime


# Params
number_hero = 10
standard: Literal['percentage', 'softmax'] = 'percentage'

# Load the dfs
folder_path = 'Counter Result'
file_list = [f for f in os.listdir(folder_path) if f.endswith('.xlsx') or f.endswith('.xls')]


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
# Sort the list of filenames based on the extracted date and suffix
file_list = sorted(file_list, key=extract_date_and_suffix)


df_list = []
for file in file_list:
    file_path = os.path.join(folder_path, file)
    df = pd.read_excel(file_path)
    df_list.append(df)


# Top {number_hero} heroes
top_hero_list = []
for df in df_list:
    top_hero_list += df['Unnamed: 4'].iloc[:number_hero].to_list()
top_hero_list = list(set(top_hero_list))


# Extract counteraility value of top heroes
counterability_dict = {key: [] for key in top_hero_list}
for df in df_list:
    for hero in list(counterability_dict.keys()):
        counterability_dict[hero].append(df[df['Unnamed: 4'] == hero]['Total weakness'].iloc[0])


# Filter positive value only
x = np.arange(0,len(df_list))
y = np.array(list(counterability_dict.values()))
labels = np.array(list(counterability_dict.keys()))
y_pos = [np.where(y_data > 0, y_data, 0) for y_data in y]


# Normalize the data to prevent extreme value ruin the chart
def percentage_normalize(x, axis=0):
    sum_x = np.sum(x, axis=axis, keepdims=True)
    return x / sum_x
def softmax_normalize(x, axis=0):
    e_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return e_x / np.sum(e_x, axis=axis, keepdims=True)

if standard == 'percentage':
    percent_ypos = percentage_normalize(y_pos, axis=0)
elif standard == 'softmax':
    percent_ypos = softmax_normalize(y_pos, axis=0)

# Truncate the label if too long
def truncate_label(label):
    # Check if the label contains spaces
    if ' ' in label:
        # Truncate at the first space
        truncated = label.split(' ')[0]
        return truncated + '...'  # Indicate that the label is truncated
    return label
truncated_labels = [truncate_label(label) for label in labels]

# Sort the data and the label
sequences_and_labels = sorted(zip(y_pos, truncated_labels), key=lambda sl: np.nansum(sl[0]), reverse=True)
percent_ypos, truncated_labels = zip(*sequences_and_labels)

# Visualize the data
plt.stackplot(x, *percent_ypos, labels=labels)
plt.xlabel('Past Days')
plt.ylabel('Total weakness')
plt.title(f'Top {number_hero} Counter')
xticks = plt.gca().get_xticks()
xtick_labels = [str(int(label)) for label in xticks]
inverted_labels = xtick_labels[::-1]
plt.gca().xaxis.set_major_locator(plt.FixedLocator(xticks))
plt.gca().xaxis.set_major_formatter(plt.FixedFormatter(inverted_labels))
handles, labels = plt.gca().get_legend_handles_labels()
plt.legend(handles=handles[::-1], labels=labels[::-1], loc='upper left', bbox_to_anchor=(1, 1))  # Adjust legend position if necessary
plt.show()