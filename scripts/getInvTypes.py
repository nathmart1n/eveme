"""
Helper python file to refresh typeIDs JSON
"""
import requests
import pandas as pd
import json

print('Beginning file download with requests')

# Query fuzzwork for latest invTypes.csv
url = 'https://www.fuzzwork.co.uk/dump/latest/invTypes.csv'
r = requests.get(url)

# Write to our temp folder
with open('temp/invTypes.csv', 'wb') as f:
    f.write(r.content)

# Read in to pandas dataframe
df = pd.read_csv('temp/invTypes.csv')
# Dropping description column since it doesn't parse correctly.
del df['description']
# Set index as typeID since we want our JSON used as a dict that takes in ID and outputs name
df = df.set_index('typeID')
# Setting as a dict allows us to transform to JSON easily
df = df.to_dict('index')

# Write to JSON static file location
with open('eveme/static/json/invTypes.json', 'w') as fp:
    json.dump(df, fp, indent=4, sort_keys=True)

print('invTypes.json updated')
