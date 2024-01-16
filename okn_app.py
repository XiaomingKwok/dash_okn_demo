import json
import plotly.express as px
import urllib.request as urllib
from dash import Dash, dcc, html, Input, Output, State, callback
import plotly.express as px

# from urllib.request import urlopen
import pandas as pd
import plotly.graph_objs as go
import statsmodels.api as sm
import plotly.figure_factory as ff
import numpy as np
import os
import requests
import createMap
import branca.colormap as cm
import folium

from gpt_helper import Neo4jGPTQuery
from utils import import_config

from dash.exceptions import PreventUpdate

default_map_location = 'maps/default_map.html'
with open(default_map_location, 'r', encoding='utf-8') as file:
    default_map_html = file.read()
config = import_config("config.ini")
openai_key = config["openai_key"]
neo4j_url = config["neo4j_url"]
neo4j_user = config["neo4j_user"]
neo4j_password = config["neo4j_password"]

gds_db = Neo4jGPTQuery(
        url=neo4j_url,
        user=neo4j_user,
        password=neo4j_password,
        openai_api_key=openai_key,
    )

# mapbox_access_token = "pk.eyJ1Ijoic3RlZmZlbmhpbGwiLCJhIjoiY2ttc3p6ODlrMG1ybzJwcG10d3hoaDZndCJ9.YE2gGNJiw6deBuFgHRHPjg"

us_geo = json.load(open("msa.geojson", "r", encoding="utf-8"))
df = pd.read_csv("county-data.csv")

app = Dash(__name__)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="infoForMap"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src=app.get_asset_url("pngkey.com-alabama-crimson-tide-logo-818812.png"),
                            id="plotly-image",
                            style={
                                "height": "60px",
                                "width": "auto",
                                "margin-bottom": "25px",
                            },
                        )
                    ],
                    className="one-third column",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4(
                                    "OKN Project - Health, Justice, and Household in Rural Areas",
                                    style={"font-weight": "bold"},
                                ),
                                # html.H5(
                                #     "Analysis of the relationship between nutritional patterns and \n the health status within the countries",
                                #     style={"margin-top": "0px"},
                                # ),
                            ]
                        )
                    ],
                    className="three column",
                    id="title",
                ),
                html.Div(
                    # create empty div for align cente
                    className="one-third column",
                ),
            ],
            id="header",
            className="row flex-display",
            style={"margin-bottom": "25px"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            "Query",
                            className="control_label",
                            style={"text-align": "center", "font-weight": "bold"},
                        ),
                        html.P(
                            "Please provide a concise and straightforward query. For example:"
                            " What is the average mortgage amount for single-family homes compared to multi-family units?",
                            className="control_label",
                            style={"text-align": "justify"},
                        ),
                        html.P(),
                        dcc.Textarea(
                            id='textarea-query',
                            value='',
                            style={'width': '100%', 'height': '10vh'},
                        ),
                        html.Button('Submit', id='textarea-query-button', n_clicks=0),
                        html.P(),
                        html.P(
                            "Answer",
                            className="control_label",
                            style={"text-align": "center", "font-weight": "bold"},
                        ),
                        dcc.Textarea(
                            id='textarea-answer',
                            value='',
                            style={'width': '100%', 'height': '30vh', 'backgroundColor': '#f2f2f2',},
                            readOnly=True,
                        ),
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                    style={"text-align": "justify"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(id="well_text"),
                                        html.P(
                                            "Maximum",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                            },
                                        ),
                                        html.P(
                                            id="max_name",
                                            style={"text-align": "center"},
                                        ),
                                        html.P(
                                            id="max_value",
                                            style={"text-align": "center"},
                                        ),
                                    ],
                                    className="mini_container",
                                    id="wells",
                                ),
                                html.Div(
                                    [
                                        html.P(id="gasText"),
                                        html.P(
                                            "Minimum",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                            },
                                        ),
                                        html.P(
                                            id="min_name",
                                            style={"text-align": "center"},
                                        ),
                                        html.P(
                                            id="min_value",
                                            style={"text-align": "center"},
                                        ),
                                    ],
                                    className="mini_container",
                                    id="gas",
                                ),
                                html.Div(
                                    [
                                        html.P(id="oilText"),
                                        html.P(
                                            "Mean",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                            },
                                        ),
                                        html.P(
                                            id="mean", style={"text-align": "center"}
                                        ),
                                        html.P(
                                            "Standard deviation",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                            },
                                        ),
                                        html.P(
                                            id="st_dev", style={"text-align": "center"}
                                        ),
                                    ],
                                    # ,
                                    className="mini_container",
                                    id="oil",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),
                        html.Div(
                            [html.Iframe(id="choropleth", srcDoc=default_map_html,
                                         style={'width': '100%', 'height': '500px'})],
                            # id="countGraphContainer",
                            className="pretty_container",
                        ),
                    ],
                    id="right-column",
                    className="eight columns",
                ),
            ],
            className="row flex-display",
        ),

    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

colors = [
    "#0d0887",
    "#46039f",
    "#7201a8",
    "#9c179e",
    "#bd3786",
    "#d8576b",
    "#ed7953",
    "#fb9f3a",
    "#fdca26",
    "#f0f921",
]
colors2 = ["#fdca26", "#ed7953", "#bd3786", "#7201a8", "#0d0887"]


# @callback(
#     Output('textarea-answer', 'value'),
#     Input('textarea-query-button', 'n_clicks'),
#     State('textarea-query', 'value')
# )
@callback(
    [Output('textarea-answer', 'value'),
     Output('infoForMap', 'data')], 
    Input('textarea-query-button', 'n_clicks'),
    State('textarea-query', 'value')
)
def update_output(n_clicks, value):
    if n_clicks > 0:
        res, city_res = gds_db.run(value)
        flattened_res = [str(item) for sublist in res for item in sublist]
        answer = ''.join(flattened_res)
        print("city_res")
        print(city_res)
        return answer, city_res
    else:
        return ' ', {}
    
@app.callback(
    Output("choropleth", "srcDoc"),
    Input('infoForMap', 'data')
)
def update_map(map_data):
    if map_data:  
        print(map_data)

        florida_crime = json.loads(map_data)

        if isinstance(florida_crime, dict):
            florida_crime_df = pd.DataFrame(list(florida_crime.items()), columns=['Key', 'Value'])
            color = ['blue']
            if len(florida_crime_df) > 1:
                color = ['blue', 'red']

        elif isinstance(florida_crime, list):
            florida_crime_df = pd.DataFrame(florida_crime, columns=['Key'])

        hasValues = any(florida_crime_df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)))
        # description = "2022 Violent crime rate per 100k"
        description=" "

        area_type = 'cbsa'
        map_html, mergedData = createMap.CreateMap(area_type, florida_crime, hasValues, description, color)
        map_iframe = html.Iframe(srcDoc=map_html, width='100%', height='500px')
        return map_html

    else:
        return default_map_html


if __name__ == "__main__":
    app.run(debug=True, port=8050)
