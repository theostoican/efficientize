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
    numElemBarChart = 10
    numElemPieChart = 6

    with open(timeStatsFile, 'r') as timeStatsIn:
        csvReader = csv.DictReader(timeStatsIn)
        totalTime = 0

        for row in csvReader:
            window = row["window"]
            time = -(float)(row["time"])
            totalTime += -time
            heapq.heappush(timeStatsHeap, (time, window))
        
        # Sanity check: existent but empty file
        if len(timeStatsHeap) == 0:
            return '404'
        
        # Variables for bar chart
        topStats = [heapq.heappop(timeStatsHeap) for i in range(0, min(len(timeStatsHeap), numElemBarChart))]
        yData = [splitTextIntoHtmlLines(window) for (time, window) in topStats]
        barTextData = [window + '<br>' + str(datetime.timedelta(seconds = int(-time))) for (time, window) in topStats]
        xData = [int(-time) for (time, window) in topStats]
        maxBarValue = max(xData)
        tickValues = [int(i * maxBarValue / xAxisNumPoints) for i in range(0, xAxisNumPoints + 1)]
        tickText = list(map(lambda secs : str(datetime.timedelta(seconds = secs)), tickValues))

        # Variables for pie chart
        pieWihoutOthersSecs = sum(list(map(lambda p : -p[0], topStats[:min(len(topStats), numElemPieChart - 1)])))
        othersSecs = int(totalTime - pieWihoutOthersSecs)

        pieValues = [xData[i] for i in range(0, min(len(xData), numElemPieChart - 1))]
        totalPieTime = str(datetime.timedelta(seconds = othersSecs + sum(pieValues)))
        pieValues.append(othersSecs)

        pieTextData = [barTextData[i] for i in range(0, min(len(barTextData), numElemPieChart - 1))]
        pieTextData.append("Others" + '<br>' + str(datetime.timedelta(seconds = othersSecs)))

        pieLabels = [yData[i] for i in range(0, min(len(yData), numElemPieChart - 1))]
        pieLabels.append("Others")
        
        print(pieLabels)

        layout = html.Div([
            html.Center(html.H3("Time usage statistics (" + selectedDate + ")" + " - " + totalPieTime)),
            dcc.Graph(
                id='time-stats-pie-chart',
                figure={
                    'data': [
                        go.Pie(
                            labels = pieLabels,
                            values = pieValues,
                            text = pieTextData,
                            textinfo = 'percent',
                            hoverinfo='text',
                            ),
                    ],
                    'layout': go.Layout(
                        height = 350,
                        margin = dict(t = 10, b = 10),
                        hovermode = 'closest',
                    )
                }
            ),
            dcc.Graph(
                id='time-stats-bar-chart',
                figure={
                    'data': [
                        go.Bar(
                            x = xData,
                            y = yData,
                            text = barTextData,
                            width = [0.5 for i in range(0, len(xData))],
                            orientation = 'h',
                            hoverinfo='text',
                        )
                    ],
                    'layout': go.Layout(
                        xaxis = dict(
                            tickvals = tickValues,
                            ticktext = tickText
                        ),
                        yaxis = dict(
                            # Trick to slide to the left the yaxis labels
                            ticks = 'outside',
                            tickcolor = 'rgba(0,0,0,0)'
                        ),
                        height=550,
                        hovermode = 'closest',
                        margin = dict(l=200, r=40, t=0, b=30),
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