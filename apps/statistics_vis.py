import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import heapq
import csv
import datetime
import textwrap
from functools import reduce

import config
from app import app

def splitTextIntoHtmlLines(text):
    maxCharsPerLines = 30
    if len(text) > 75:
        text = text[:75] + '...'
    print(len(text))
    lines = textwrap.wrap(text, maxCharsPerLines)
    
    if len(lines) == 0:
        return text

    brLines = reduce(lambda partialLines, line : partialLines + '<br>' + line, lines)

    return brLines

def getStatisticsLayout(selectedDate):
    timeStatsFile = config.LOGS_DIR + config.TIME_DIR + selectedDate
    timeStatsHeap = []
    xAxisNumPoints = 5

    with open(timeStatsFile, 'r') as timeStatsIn:
        csvReader = csv.DictReader(timeStatsIn)

        for row in csvReader:
            window = row["window"]
            time = -(float)(row["time"])
            heapq.heappush(timeStatsHeap, (time, window))
        
        #Error when heap empty TODO
        topStats = [heapq.heappop(timeStatsHeap) for i in range(0, min(len(timeStatsHeap), 10))]
        yData = [splitTextIntoHtmlLines(window) for (time, window) in topStats]
        textData = [window + '<br>' + str(datetime.timedelta(seconds = int(-time))) for (time, window) in topStats]
        #tickText = [str(datetime.timedelta(seconds = int(-time))) for (time, window) in topStats]
        xData = [int(-time) for (time, window) in topStats]
        maxBarValue = max(xData)
        tickValues = [int(i * maxBarValue / xAxisNumPoints) for i in range(0, xAxisNumPoints + 1)]
        tickText = list(map(lambda secs : str(datetime.timedelta(seconds = secs)), tickValues))

        # str(datetime.timedelta(seconds=-time))
        print(topStats)
        print(xData)

        layout = html.Div([
            html.H3('App 1'),
            dcc.Graph(
                id='example-graph',
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                        {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
                    ],
                    'layout': {
                        'title': 'Dash Data Visualization'
                    }
                }
            ),
            dcc.Graph(
                id='time-stats-bar-chart',
                figure={
                    'data': [
                        go.Bar(
                            x = xData,
                            y = yData,
                            text = textData,
                            width = [0.5 for i in range(0, len(xData))],
                            orientation = 'h',
                            hoverinfo='text',
                            #width = 4
                        )
                    ],
                    'layout': go.Layout(
                        title = 'Dash Data Visualization',
                        xaxis = dict(
                            tickvals = tickValues,
                            ticktext = tickText
                        ),
                        yaxis = dict(
                            # Trick to slide to the left the yaxis labels
                            ticks = 'outside',
                            tickcolor = 'rgba(0,0,0,0)'
                        ),
                        height=700,
                        hovermode = 'closest',
                        margin = dict(l=200, r=40, t=40, b=30),
                    )
                }
            ),
            html.Div(id='app-1-display-value'),
            dcc.Link('Go Home', href='/')
        ])

        return layout


@app.callback(
    Output('app-1-display-value', 'children'),
    [Input('app-1-dropdown', 'value')])
def display_value(value):
    return 'You have selected "{}"'.format(value)