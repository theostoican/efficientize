import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import csv
from random import randint

import config
from app import app

def getTimelineLayout(fileName):
    x_data = []
    y_data = []
    text_data = []
    color_data = []
    pathToFile = config.LOGS_DIR + config.TIMELINE_DIR + fileName

    with open(pathToFile, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        # Read data and prepare it for visualization
        for row in csv_reader:
            x_data.append((row["start"], row["finish"]))
            y_data.append(2)
            text_data.append(row["window"])

            #text_data.append('Start time: ' + str(row["start"]) + \
            #        ', Finish time: ' + str(row["finish"]))
            color = (randint(0, 255), randint(0, 255), randint(0, 255))
            color_data.append('rgb' + str(color))

        # Return the layout with the correspondent data
        return html.Div([
            html.H1('Page 1'),
            html.Div(id='page-1-content'),
            dcc.Graph(
            figure=go.Figure(
                data=[
                    go.Bar(
                        x=x_data,
                        y=y_data,
                        text=text_data,
                        name='Rest of world',
                        marker=dict(
                            color=color_data
                        )
                    )
                ],
                layout=go.Layout(
                    title='US Export of Plastic Scrap',
                    xaxis=dict(type='category'),
                    showlegend=True,
                    legend=dict (
                        x=0,
                        y=1.0
                    ),
                    margin=dict(l=40, r=0, t=40, b=30)
                )
            ),
            style={'height': 300},
            id='my-graph'
            ),
            html.Br(),
            dcc.Link('Go back to home', href='/'),
        ])

@app.callback(dash.dependencies.Output('page-1-content', 'children'),
              [dash.dependencies.Input('page-1-dropdown', 'value')])
def page_1_dropdown(value):
    return 'You have selected "{}"'.format(value)