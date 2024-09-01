import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import math
import re
from datetime import datetime

# Params
number_hero = 10


# Load the dfs
mainfolder_path = 'Meta Result'
subfolder_path = 'Mythical Glory+'
folder_path = mainfolder_path + '/' + subfolder_path
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
    df = df.sort_values(by='Pick Rate', ascending=False)
    df_list.append(df)


# Top {number_hero} heroes
top_hero_list = []
for df in df_list:
    top_hero_list += df['Hero'].iloc[:number_hero].to_list()
top_hero_list = list(set(top_hero_list))


# Extract popular value of top heroes
popular_dict = {key: [] for key in top_hero_list}
for df in df_list:
    for hero in list(popular_dict.keys()):
        popular_dict[hero].append(df[df['Hero'] == hero]['Pick Rate'].iloc[0])


# Filter positive value only
x = np.arange(0,len(df_list))
y = np.array(list(popular_dict.values()))
labels = np.array(list(popular_dict.keys()))
y = np.char.replace(y, '%', '').astype(float)
y_pos = [np.where(y_data > 0, y_data, 0) for y_data in y]


# Normalize the data to prevent extreme value ruin the chart
def percentage_normalize(x, axis=0):
    sum_x = np.sum(x, axis=axis, keepdims=True)
    return x / sum_x
percent_ypos = y_pos


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
sequences_and_labels = sorted(zip(percent_ypos, truncated_labels), key=lambda sl: np.nansum(sl[0]), reverse=True)
percent_ypos, truncated_labels = zip(*sequences_and_labels)

# Visualize the data
legend_ncol = math.ceil(len(top_hero_list) / 25)  
fig, ax = plt.subplots(figsize=(7+2*legend_ncol,7))
stacks = ax.stackplot(x, *percent_ypos, labels=truncated_labels)
hatch_patterns = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '*', '.']
group_size = 10  # Define the size of each group
for i, collection in enumerate(ax.collections):
    # Determine the hatch pattern for this collection based on its index
    hatch_pattern = hatch_patterns[(i // group_size) % len(hatch_patterns)]
    collection.set_edgecolor('black')
    collection.set_hatch(hatch_pattern)
# Customize x-axis labels
xticks = ax.get_xticks()
xtick_labels = [str(int(label)) for label in xticks]
inverted_labels = xtick_labels[::-1]
ax.xaxis.set_major_locator(plt.FixedLocator(xticks))
ax.xaxis.set_major_formatter(plt.FixedFormatter(inverted_labels))
# Handle the legend
handles, labels = ax.get_legend_handles_labels()
legend = ax.legend(
    handles[::-1], labels[::-1], loc='upper left', bbox_to_anchor=(1, 1), ncol=legend_ncol,
    handlelength=3.0,  # Length of the legend handle
    handleheight=2,  # Height of the legend handle
    borderpad=0.5,     # Padding between the legend border and the handles
    columnspacing=0.5, # Spacing between columns
    labelspacing=0.5   # Spacing between legend labels
)
plt.tight_layout()
# Add labels and title
plt.xlabel('Past Days')
plt.ylabel('Metability')
plt.title(f'Top {number_hero} Meta for {subfolder_path}')
plt.show()
