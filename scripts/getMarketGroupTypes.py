"""
Helper python file that gets all typeIDs in each market group with typeIDs
"""
import requests
import pandas as pd
import json
import os
import pathlib
import sys

print('Beginning file download with requests')

json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
invTypes = dict(json.load(open(json_url)))

url = 'https://www.fuzzwork.co.uk/dump/latest/invTypes.csv'
r = requests.get(url)

with open('temp/invTypes.csv', 'wb') as f:
    f.write(r.content)

df = pd.read_csv('temp/invTypes.csv')

df_copy = df[df['marketGroupID'] == '1696']

marketGroupTypes = df.groupby('marketGroupID')['typeID'].apply(list).to_dict()

with open('eveme/static/json/marketGroupTypes.json', 'w') as fp:
    json.dump(marketGroupTypes, fp, indent=4, sort_keys=True)
