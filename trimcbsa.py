import geopandas as gpd
import createMap
import os
import json

# Load the GeoJSON file
# gdf = gpd.read_file('C:\\Users\\ryanw\PycharmProjects\dash_okn_demo\geojson\CBSA_trimmed.geojson')
# gdf = gdf.drop(columns=['csafp', 'aland', 'awater'])
# gdf.to_file('C:\\Users\\ryanw\PycharmProjects\dash_okn_demo\geojson\CBSA_trimmed.geojson', driver='GeoJSON')

path = "C:\\Users\\ryanw\PycharmProjects\dash_okn_demo\\"
# json_file_path = os.path.join(path, 'floridaViolentCrimeData.json')
json_file_path = os.path.join(path, 'fake_cbsa_data2.json')

with open(json_file_path, 'r') as file:
    florida_crime = json.load(file)


mapLocation, data = createMap.CreateMap("cbsa",florida_crime, False, "These are what I selected", "blue")
