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

json_url = os.path.join(pathlib.Path().resolve(), "eveme/static/json", "marketGroupTypes.json")
marketGroupTypes = dict(json.load(open(json_url)))

url = 'https://www.fuzzwork.co.uk/dump/latest/invMarketGroups.csv'
r = requests.get(url)

with open('marketGroups.csv', 'wb') as f:
    f.write(r.content)

df_marketGroups = pd.read_csv('marketGroups.csv')
idToName = pd.Series(df_marketGroups['marketGroupName'].values, index=df_marketGroups['marketGroupID']).to_dict()
idToName = {str(key): value for key, value in idToName.items()}
idToName['None'] = 'None'

df_marketGroups['marketGroupID'] = df_marketGroups['marketGroupID'].astype('string')

marketGroups = df_marketGroups['marketGroupID'].tolist()
parentGroups = df_marketGroups['parentGroupID'].tolist()
# Convert groups to their names from IDs
# parentGroups = [idToName[k] for k in parentGroups]
# Join parent with child in single list
zippedGroups = list(zip(parentGroups, marketGroups))
# Get our root groups
root_nodes = {x[1] for x in zippedGroups if x[0] == "None"}


def get_nodes(node):
    d = {}
    # d['id'] = node
    children = get_children(node)
    if children:
        dicts = [get_nodes(child) for child in children]
        children = [idToName[child] for child in children]
        d = dict(zip(children, dicts))
    else:
        print(type(node))
        d = dict.fromkeys(marketGroupTypes[node])
    return d


def get_children(node):
    return [x[1] for x in zippedGroups if x[0] == node]


tree = get_nodes('None')
print(sorted(root_nodes))

# groups = tree['None']
# Not working for group 1697

with open('eveme/static/json/marketGroups.json', 'w') as fp:
    json.dump(tree, fp, indent=4, sort_keys=True)
