import folium
from folium.features import GeoJsonTooltip
import geopandas as gpd
import pandas as pd
import branca.colormap as cm
import lookupCodes
import os
import plotly.express as px
import dash
from dash import dcc
from dash import html
import json
import uuid


def parse_county_state(input_string):
    # Split the string into county and state based on the comma
    parts = input_string.split(',')

    # Trim any leading or trailing whitespace
    county = parts[0].strip()
    state = parts[1].strip() if len(parts) > 1 else None

    return county, state


def CreateMap(areaType, data, hasValues, description, color):

    dataLen = len(data)
    isCounty = False
    isState = False
    isCBSA = False

    if areaType.lower() == 'county':
        geojson_location = os.path.join('geojson', 'counties.geojson')
        county_location = os.path.join("codes", "st01_al_cou2020.txt")
        isCounty = True
    elif areaType.lower() == 'state':
        geojson_location = os.path.join('geojson', 'states.geojson')
        isState = True
    else:
        # geojson_location = 'geojson\CBSA.geojson'
        # geojson_location = 'geojson\CBSA_smaller.geojson'
        geojson_location = os.path.join('geojson', 'CBSA.geojson')
        cbsafp_location = os.path.join("codes", "cbsa2fipsxw.txt")
        isCBSA = True

    if isCounty:
        counties = [""] * dataLen
        states = [""] * dataLen
        countyns = [""] * dataLen
        paramName = 'COUNTYNS'
        tooltipAlias = 'County: '

    if isCBSA:
        areas = [""] * dataLen
        paramName = 'CBSAFP'
        tooltipAlias = 'CBSA Name: '

    nameField = 'NAME'

    values = [0] * dataLen
    i = 0

    if hasValues:
        if isCounty:
            for key, value in data.items():
                counties[i], states[i] = parse_county_state(key)
                values[i] = value
                countyns[i] = str(lookupCodes.find_countyns(county_location, counties[i], states[i])).zfill(8)
                i += 1
            df_key = countyns

        if isCBSA:
            for key, value in data.items():
                areas[i] = key
                values[i] = value
                i += 1
            df_key = areas

    else:
        if isCounty:
            for key in data:
                counties[i], states[i] = parse_county_state(key)
                countyns[i] = str(lookupCodes.find_countyns(county_location, counties[i], states[i])).zfill(8)
                i += 1
            df_key = countyns

        if isCBSA:
            df_key = data

    if hasValues and dataLen >= 2:
        gradient = True
    else:
        gradient = False



    def select_style_function(merged, paramName):
        def style_function(feature):
            if feature['properties'][paramName] in merged[paramName].values:
                return {'fillColor': color, 'color': 'gray'}
            else:
                return {'fillColor': 'gray', 'color': 'gray'}
        return style_function

    def gradient_style_function(merged, paramName):
        def style_function(feature):
            value = merged.loc[merged[paramName] == feature['properties'][paramName], 'VALUE']
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
    data_df = pd.DataFrame({paramName: df_key, 'VALUE': values})

    gdf = gpd.read_file(geojson_location)

    # gdf.to_file('geojson\\CBSA_smallest.geojson', driver='GeoJSON')

    merged = gdf.merge(data_df, on=paramName)

    if gradient:
        max_value = max(merged['VALUE'])
        min_value = min(merged['VALUE'])
        color_scale = cm.LinearColormap(color, vmin=min_value, vmax=max_value)
        # color_scale = color.scale(min_value, max_value)
        # colormap = cm.LinearColormap(color_scale, vmin= min_value, vmax=max_value)
        # colormap.save('colormap.html')

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

    if hasValues:
        tooltip = GeoJsonTooltip(
            fields=[nameField, 'VALUE'],
            aliases=[tooltipAlias, description + ': '],  #Displayed text before the value
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
    else:
        tooltip = GeoJsonTooltip(
            fields=[nameField],
            aliases=[tooltipAlias],  # Displayed text before the value
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
        my_style_function = gradient_style_function(merged, paramName)
    else:
        my_style_function = select_style_function(merged, paramName)

    # mergedProjected = merged.to_crs('EPSG:5070')

    mapX = merged.centroid.y.median()
    mapY = merged.centroid.x.median()

    minY, minX, _, _ = merged.bounds.min()
    _, _, maxY, maxX = merged.bounds.max()

    rangeX = maxX - minX
    rangeY = maxY - minY

    swCorner = [minX, minY]
    neCorner = [maxX, maxY]

    # maxRange = max(rangeX, rangeY)

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

    if gradient:
        m.add_child(color_scale)

    # mapFilename = f'map_{uuid.uuid4()}.html'
    #
    # # Save the map
    # m.save(os.path.join("maps", mapFilename))
    #
    # return "http://localhost:8000/maps/" + mapFilename, merged

    map_html =m._repr_html_()

    return map_html, merged




