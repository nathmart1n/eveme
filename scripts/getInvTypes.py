"""
Helper python file to refresh typeIDs JSON
"""
import requests
import pandas as pd
import json

print('Beginning file download with requests')

url = 'https://www.fuzzwork.co.uk/dump/latest/invTypes.csv'
r = requests.get(url)

with open('../invTypes.csv', 'wb') as f:
    f.write(r.content)

df = pd.read_csv('invTypes.csv')
# Dropping description column since it doesn't parse correctly.
del df['description']
df = df.set_index('typeID')
df = df.to_dict('index')

with open('eveme/static/json/invTypes.json', 'w') as fp:
    json.dump(df, fp, indent=4, sort_keys=True)
