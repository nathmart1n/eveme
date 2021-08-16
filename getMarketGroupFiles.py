"""
Helper python file to refresh typeIDs JSON
"""
import requests
import pandas as pd
import json
import os
import pathlib
import sys

print('Beginning file download with requests')

url = 'https://esi.evetech.net/latest/markets/groups'
r = requests.get(url).json()

groups = []

if 1697 in r:
    print('Yes')

keys = ['marketGroupID', 'parentGroupID', 'marketGroupName', 'hasTypes']
num = 0
for group in r:
    url = 'https://esi.evetech.net/latest/markets/groups/{}/'.format(group)
    res = requests.get(url).json()
    parent = ''
    if 'parent_group_id' not in res.items():
        parent = 'None'
    else:
        parent = res['parent_group_id']
    hasTypes = True
    if res['types'] != []:
        hasTypes = False
    groups.append([group, parent, res['name'], res['description'], hasTypes])
    num += 1
    print(num)
print(len(groups))
df = pd.DataFrame(groups, columns=keys)
print(df)
# with open('eveme/static/json/marketGroupsRaw.json', 'w') as fp:
#     json.dump(r, fp, indent=4, sort_keys=True)
