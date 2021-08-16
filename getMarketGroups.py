"""
Helper python file to refresh typeIDs JSON
"""
import requests
import pandas as pd
import json
import os
import pathlib


def subtree(node, relationships):
    return {
        v: subtree(v, relationships)
        for v in [x[0] for x in relationships if x[1] == node]
    }


print('Beginning file download with requests')

json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "invTypes.json")
invTypes = dict(json.load(open(json_url)))

url = 'https://www.fuzzwork.co.uk/dump/latest/invMarketGroups.csv'
r = requests.get(url)

with open('marketGroups.csv', 'wb') as f:
    f.write(r.content)


df_marketGroups = pd.read_csv('marketGroups.csv')

groupIdToName = pd.Series(df_marketGroups.marketGroupName.values, index=df_marketGroups.marketGroupID).to_dict()
groupIdToName[-1] = 'None'
print(df_marketGroups)

df_marketGroups['parentGroupID'] = df_marketGroups['parentGroupID'].replace('None', -1)
df_marketGroups['parentGroupID'] = df_marketGroups['parentGroupID'].astype('int64')

df_marketGroups['parentGroupName'] = df_marketGroups['parentGroupID'].map(groupIdToName)


# with open('eveme/static/json/marketGroups.json', 'w') as fp:
#    json.dump(groupsJson, fp, indent=4, sort_keys=True)
