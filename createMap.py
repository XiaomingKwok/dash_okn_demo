import folium
from folium.features import GeoJsonTooltip
import geopandas as gpd
import pandas as pd
import branca.colormap as cm
import lookupCountyns
import os
import plotly.express as px
import dash
from dash import dcc
from dash import html
import json


def parse_county_state(input_string):
    # Split the string into county and state based on the comma
    parts = input_string.split(',')

    # Trim any leading or trailing whitespace
    county = parts[0].strip()
    state = parts[1].strip() if len(parts) > 1 else None

    return county, state


def CreateMap(data, hasValues, description, color):

    dataLen = len(data)

    geojson_location = 'C:\\Users\\ryanw\PycharmProjects\InteractiveMap\geojson\counties.geojson'
    county_location = os.path.join("stateCodes", "st01_al_cou2020.txt")

    counties = [""] * dataLen
    states = [""] * dataLen
    countyns = [""] * dataLen
    values = [0] * dataLen
    i = 0

    for key, value in data.items():
        counties[i], states[i] = parse_county_state(key)
        values[i] = value
        countyns[i] = str(lookupCountyns.find_countyns(county_location, counties[i], states[i])).zfill(8)
        i += 1

    if hasValues and dataLen >= 2:
        gradient = True
    else:
        gradient = False

    if gradient:
        max_value = max(values)
        min_value = min(values)
        color_scale = color.scale(min_value, max_value)

    def select_style_function(merged):
        def style_function(feature):
            if feature['properties']['COUNTYNS'] in merged['COUNTYNS'].values:
                return {'fillColor': 'blue', 'color': 'gray'}
            else:
                return {'fillColor': 'gray', 'color': 'gray'}

        return style_function

    def gradient_style_function(merged):
        def style_function(feature):
            value = merged.loc[merged['COUNTYNS'] == feature['properties']['COUNTYNS'], 'VALUE']
            if value.size == 0:
                return {
                    'fillColor': 'gray',
                    'color': 'black',
                    'weight': 1,
                    'dashArray': '5, 5',
                    'fillOpacity': 0
                }
            else:
                value = value.values[0]
                return {
                    'fillColor': color_scale(value),
                    'color': 'black',
                    'weight': 1,
                    'dashArray': '5, 5',
                    'fillOpacity': 0.6
                }
        return style_function

    # Create a Folium map

    data_df = pd.DataFrame({'COUNTYNS': countyns, 'VALUE': values})

    gdf = gpd.read_file(geojson_location)
    merged = gdf.merge(data_df, on='COUNTYNS')

    # fig = px.choropleth(merged, geojson=merged, locations=merged.index, color='VALUE',
    #                     color_continuous_scale='Viridis')
    #
    # #fig = px.line_geo(lat=[0,15,20,35], lon=[5,10,25,30])
    #
    # fig.update_geos(fitbounds="locations")
    # fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})
    #
    # app.layout = html.Div([dcc.Graph(figure=fig)])
    #
    # app.run_server(debug=True, port=8050)





    tooltip = GeoJsonTooltip(
        fields=['NAME', 'VALUE'],
        aliases=['County: ', description + ': '],  #Displayed text before the value
        localize=True,
        sticky=False,
        labels=True,
        style="""
            background-color: #F0EFEF;
            border: 2px solid black;
            border-radius: 3px;
            box-shadow: 3px;
        """,
        max_width=800,
    )

    # Add Choropleth layer
    if gradient:
        my_style_function = gradient_style_function(merged)
    else:
        my_style_function = select_style_function(merged)

    mergedProjected = merged.to_crs('EPSG:5070')

    mapX = merged.centroid.y.median()
    mapY = merged.centroid.x.median()

    minY, minX, _, _ = merged.bounds.min()
    _, _, maxY, maxX = merged.bounds.max()

    rangeX = maxX - minX
    rangeY = maxY - minY

    swCorner = [minX, minY]
    neCorner = [maxX, maxY]

    maxRange = max(rangeX, rangeY)

    #print("The distance in x is %f", maxRange)

    zoomLevel = 10

    m = folium.Map(location=[mapX, mapY], zoom_start=zoomLevel)
    #m = folium.Map(location=[37.0902, -95.7129], zoom_start=5)

    m.fit_bounds([swCorner, neCorner])

    folium.GeoJson(
        merged,
        style_function=my_style_function,
        tooltip=tooltip
    ).add_to(m)

    # Save the map
    m.save('example.html')

    return "http://localhost:8000/example.html", merged



