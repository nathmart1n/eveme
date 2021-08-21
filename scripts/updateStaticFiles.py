"""
Helper python file to pull some needed static files.
"""
import requests
import pandas as pd
import json
import os
import pathlib


# these functions are from stackoverflow, don't really understand but it works
def get_nodes(node):
    d = {}
    # d['id'] = node
    children = get_children(node)
    if children:
        dicts = [get_nodes(child) for child in children]
        children = [idToName[child] for child in children]
        d = dict(zip(children, dicts))
    else:
        if node in marketGroupTypes.keys():
            for typeID in marketGroupTypes[node]:
                d[typeID] = invTypes[typeID]['typeName']
    return d


def get_children(node):
    return [x[1] for x in zippedGroups if x[0] == node]


print('Beginning file download from fuzzwork with requests')

# Query fuzzwork for latest invTypes.csv
url = 'https://www.fuzzwork.co.uk/dump/latest/invTypes.csv'
r = requests.get(url)

# Write to our temp folder
with open('temp/invTypes.csv', 'wb') as f:
    f.write(r.content)

url = 'https://www.fuzzwork.co.uk/dump/latest/invMarketGroups.csv'
r = requests.get(url)

with open('temp/marketGroups.csv', 'wb') as f:
    f.write(r.content)

print('Downloaded fuzzwork files')

# Update invTypes.json
print('Updating invTypes.json')
# Read in invTypes dataframe
df = pd.read_csv('temp/invTypes.csv')
# Dropping description column since it doesn't parse correctly.
del df['description']
# Set index as typeID since we want our JSON used as a dict that takes in ID and outputs name
df = df.set_index('typeID')
# Setting as a dict allows us to transform to JSON easily
invTypes = df.to_dict('index')
# Write invTypes to JSON in static file location
with open('eveme/static/json/invTypes.json', 'w') as fp:
    json.dump(invTypes, fp, indent=4, sort_keys=True)
print('invTypes.json updated')

# Update marketGroupTypes.json
print('Updating marketGroupTypes.json')
# Read in invTypes dataframe
df = pd.read_csv('temp/invTypes.csv')
# Grouping by typeID to get list of typeIDs for each marketGroupID that has typeIDs associated with it
marketGroupTypes = df.groupby('marketGroupID')['typeID'].apply(list).to_dict()
# Write marketGroupTypes to JSON in static file location
with open('eveme/static/json/marketGroupTypes.json', 'w') as fp:
    json.dump(marketGroupTypes, fp, indent=4, sort_keys=True)
print('marketGroupTypes.json updated')

# Update marketGroups.json
print('Updating marketGroups.json')
# Load marketGroupTypes and invTypes from JSOn (FIX THIS TO USE LOCAL)

# Read in marketGroups dataframe
df_marketGroups = pd.read_csv('temp/marketGroups.csv')
# Create dict converting marketGroupID to a marketGroupName
idToName = pd.Series(df_marketGroups['marketGroupName'].values, index=df_marketGroups['marketGroupID']).to_dict()
idToName = {str(key): value for key, value in idToName.items()}
# Need this 'None' since we have a 'None' key for some parentGroups
idToName['None'] = 'None'
# Convert IDs to string because easier
df_marketGroups['marketGroupID'] = df_marketGroups['marketGroupID'].astype('string')
# Get list of both child and parent groups (marketGroups is "child" of parentGroups)
marketGroups = df_marketGroups['marketGroupID'].tolist()
parentGroups = df_marketGroups['parentGroupID'].tolist()
# Join parent with child in single list
zippedGroups = list(zip(parentGroups, marketGroups))
# Get our root groups
root_nodes = {x[1] for x in zippedGroups if x[0] == "None"}
# Execute function
tree = get_nodes('None')

with open('eveme/static/json/marketGroups.json', 'w') as fp:
    json.dump(tree, fp, indent=4, sort_keys=True)
print('marketGroups.json updated')
