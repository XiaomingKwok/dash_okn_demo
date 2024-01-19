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


def getCharacteristics(provided_data_df):
    # print('Got to function')
    maxValue = max(provided_data_df['Value'])
    minValue = min(provided_data_df['Value'])
    meanValue = provided_data_df['Value'].mean()
    if len(provided_data_df['Value']) == 1:
        stdValue = "N/A"
    else:
        stdValue = round(provided_data_df['Value'].std(), 2)
    return maxValue, minValue, meanValue, stdValue

default_map_location = 'maps/default_map.html'
with open(default_map_location, 'r', encoding='utf-8') as file:
    default_map_html = file.read()
config = import_config("config.ini")
openai_key = config["openai_key"]
neo4j_url = config["neo4j_url"]
neo4j_user = config["neo4j_user"]
neo4j_password = config["neo4j_password"]
server_host = config["server_host"]

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
                                    "OKN-A Cross-Domain Knowledge Graph to Integrate Health and Justice for Rural Resilience",
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
                            "Please provide a concise and straightforward query. For example: "
                            "What percentage of people in Detroit have a dishwasher?",
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
                                        html.P(
                                            "Location(s):",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                            },
                                        ),
                                        html.P(
                                            id="title_value",
                                            style={
                                                "text-align": "center",
                                                "font-weight": "bold",
                                                "fontSize": "20px"
                                           },
                                        ),
                                    ],
                                    className="mini_container",
                                    id="title-value",
                                    style={'width': '100%'},
                                ),
                                # html.Div(
                                #     [
                                #         html.P(id="max_text"),
                                #         html.P(
                                #             "Maximum",
                                #             style={
                                #                 "text-align": "center",
                                #                 "font-weight": "bold",
                                #             },
                                #         ),
                                #         html.P(
                                #             id="max_name",
                                #             style={"text-align": "center"},
                                #         ),
                                #         html.P(
                                #             id="max_value",
                                #             style={"text-align": "center"},
                                #         ),
                                #     ],
                                #     className="mini_container",
                                #     id="max-value",
                                #     style={'width': '33%'},
                                # ),
                                # html.Div(
                                #     [
                                #         html.P(id="min_text"),
                                #         html.P(
                                #             "Minimum",
                                #             style={
                                #                 "text-align": "center",
                                #                 "font-weight": "bold",
                                #             },
                                #         ),
                                #         html.P(
                                #             id="min_name",
                                #             style={"text-align": "center"},
                                #         ),
                                #         html.P(
                                #             id="min_value",
                                #             style={"text-align": "center"},
                                #         ),
                                #     ],
                                #     className="mini_container",
                                #     id="min-text",
                                #     style={'width': '33%'},
                                #
                                # ),
                                # html.Div(
                                #     [
                                #         html.P(id="mean_text"),
                                #         html.P(
                                #             "Mean",
                                #             style={
                                #                 "text-align": "center",
                                #                 "font-weight": "bold",
                                #             },
                                #         ),
                                #         html.P(
                                #             id="mean_value", style={"text-align": "center"}
                                #         ),
                                #         html.P(
                                #             "Standard deviation",
                                #             style={
                                #                 "text-align": "center",
                                #                 "font-weight": "bold",
                                #             },
                                #         ),
                                #         html.P(
                                #             id="std_value", style={"text-align": "center"}
                                #         ),
                                #     ],
                                #     # ,
                                #     className="mini_container",
                                #     id="mean-text",
                                #     style={'width': '33%'},
                                # ),
                            ],
                            id="info-container",
                            className="row container-display",
                            # style={'width': '100%', 'display': 'none'},
                            style={'width': '100%'},
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
    [Output("choropleth", "srcDoc"),
     Output("title_value", "children"),
     # Output("max_value", "children"),
     # Output("min_value", "children"),
     # Output("mean_value", "children"),
     # Output("std_value", "children"),
     Output('info-container', 'style')],
    Input('infoForMap', 'data')
)
def update_map(map_data):
    # max_value = min_value = mean_value = std_value = " "
    # style = {'width': '100%', 'display': 'none'}
    style = {'width': '100%'}
    title = " "
    # print("The max value hasn't been set")
    if map_data and map_data.strip():
        print(map_data)

        try:
            provided_data = json.loads(map_data)

            if isinstance(provided_data, dict):
                provided_data_df = pd.DataFrame(list(provided_data.items()), columns=['Key', 'Value'])

                # max_value, min_value, mean_value, std_value = getCharacteristics(provided_data_df)
                style = {'width': '100%'}
                # print(max_value)
                color = ['red']
                if len(provided_data_df) > 1:
                    color = ['blue', 'red']

            elif isinstance(provided_data, list):
                provided_data_df = pd.DataFrame(provided_data, columns=['Key'])

            hasValues = any(provided_data_df.dtypes.apply(lambda x: pd.api.types.is_numeric_dtype(x)))
            # description = "2022 Violent crime rate per 100k"
            description=""
            # description = "Number of people who have a dishwasher"

            area_type = 'cbsa'
            map_html, mergedData = createMap.CreateMap(area_type, provided_data, hasValues, description, color)
            # title = description + " in "
            title = description

            numLocs = len(mergedData['NAME'])
            print(f"The number of locations is {numLocs}")
            if numLocs == 1:
                title += mergedData['NAME']
            elif numLocs == 2:
                title += mergedData['NAME'][0] + " and " + mergedData['NAME'][1]
            elif numLocs != 0:
                iteration = 1
                for location_name in mergedData["NAME"]:
                    if iteration + 1 != numLocs:
                        title += location_name + ", "
                        iteration +=1
                    else:
                        title += location_name + ", and " + mergedData["NAME"][iteration]
                        break
            # map_iframe = html.Iframe(srcDoc=map_html, width='100%', height='500px')
            # return map_html, max_value, min_value, mean_value, std_value, style
            return map_html, title, style
        except json.JSONDecodeError as e:
            print(e)
            return default_map_html, title, style

    else:
        # return default_map_html, max_value, min_value, mean_value, std_value, style
        return default_map_html, title, style

if __name__ == "__main__":
    app.run(host=config["server_host"], debug=True, port=8050)
