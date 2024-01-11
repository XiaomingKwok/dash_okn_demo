# callback
# Import packages
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import pandas as pd
import plotly.express as px

# Incorporate data
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder2007.csv')

# Initialize the app
app = Dash(__name__)

# App layout
app.layout = html.Div([
    html.Div(children='My First App with Data'),
    html.Hr(),
    dcc.RadioItems(options=['pop', 'lifeExp'], value='', id='controls-and-radio-item'),
    html.Hr(),
    dash_table.DataTable(data=df.to_dict('records'), page_size=10),
    dcc.Graph(figure=px.histogram(df, x='continent', y='lifeExp', histfunc='avg'), id='controls-and-graph')
])

@callback(
    Output(component_id='controls-and-graph', component_property='figure'),
    Input(component_id='controls-and-radio-item', component_property='value')
)
def update_graph(value):
    if value not in ['pop', 'lifeExp']:
        value = 'lifeExp'
    return px.histogram(df, x='continent', y=value, histfunc='avg')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

