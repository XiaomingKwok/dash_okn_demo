import geopandas as gpd

# Load the GeoJSON file
gdf = gpd.read_file('C:\\Users\\ryanw\PycharmProjects\dash_okn_demo\geojson\CBSA_trimmed.geojson')
gdf = gdf.drop(columns=['csafp', 'aland', 'awater'])
gdf.to_file('C:\\Users\\ryanw\PycharmProjects\dash_okn_demo\geojson\CBSA_trimmed.geojson', driver='GeoJSON')
