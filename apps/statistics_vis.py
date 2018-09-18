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
    limitChars = 65

    if len(text) > limitChars:
        text = text[:limitChars] + '...'
    lines = textwrap.wrap(text, maxCharsPerLines)
    
    if len(lines) == 0:
        return text

    brLines = reduce(lambda partialLines, line : partialLines + '<br>' + line, lines)

    return brLines

def getStatisticsLayout(selectedDate, statType):
    statsFile = config.LOGS_DIR + config.STATS_DIR + selectedDate
    statsHeap = []
    timeMap = {}
    totalTime = 0
    xAxisNumPoints = 5
    numElemBarChart = 10
    numElemPieChart = 6

    with open(statsFile, 'r') as statsFin:
        csvReader = csv.DictReader(statsFin)
        totalValue = 0

        for row in csvReader:
            window = row["window"]
            if statType == 'time':
                value = -float(row["time"])
            else:
                timeMap[window] = float(row["time"])
                value = -int(row["keystrokes"])
                totalTime += timeMap[window]
            totalValue += -value
            heapq.heappush(statsHeap, (value, window))
        
        # Sanity check: existent but empty file
        if len(statsHeap) == 0:
            return '404'
        
        # Variables for bar chart
        topStats = [heapq.heappop(statsHeap) 
            for i in range(0, min(len(statsHeap), numElemBarChart))]
        
        barYData = [splitTextIntoHtmlLines(window) for (value, window) in topStats]

        if statType == 'time':          
            barXData = [int(-value) for (value, window) in topStats]
            barTextData = [window + '<br>' +
                str(datetime.timedelta(seconds = \
                    int(-value))) for (value, window) in topStats]  
        else:
            barXData = [-value for (value, window) in topStats]
            barTextData = [window + '<br>' + str(-value) + ' ('
                '{:.2f}'.format(-value / timeMap[window]) + ' keystrokes/s)' for (value, window) in topStats]

        maxBarValue = max(barXData)

        if statType == "time":
            barTickValues = [int(i * maxBarValue / xAxisNumPoints) for i in range(0, xAxisNumPoints + 1)]
            barTickText = list(map(lambda secs : str(datetime.timedelta(seconds = secs)), barTickValues))
        else:
            barTickValues = [int(i * maxBarValue / xAxisNumPoints) for i in range(0, xAxisNumPoints + 1)]
            barTickText = barTickValues

        # Variables for pie chart
        pieWihoutothersValue = sum(list(map(lambda p : -p[0], topStats[:min(len(topStats), numElemPieChart - 1)])))
        pieValues = [barXData[i] for i in range(0, min(len(barXData), numElemPieChart - 1))]

        if statType == 'time':
            othersValue = int(totalValue - pieWihoutothersValue)
            totalPieValue = str(datetime.timedelta(seconds = othersValue + sum(pieValues)))
        else:
            othersValue = totalValue - pieWihoutothersValue
            totalPieValue = str(totalValue)

        pieValues.append(othersValue)

        pieTextData = [barTextData[i] for i in range(0, min(len(barTextData), numElemPieChart - 1))]
        if statType == "time":
            pieTextData.append("Others" + '<br>' + str(datetime.timedelta(seconds = othersValue)))
        else:
            othersTime = totalTime - reduce(lambda x, y : x + y, [timeMap[window] for (value, window) in topStats])
            freq = othersTime / othersTime
            pieTextData.append("Others" + '<br>' + str(othersValue) + ' (' + 
                '{:.2f}'.format(freq) + " keystrokes/s)")
        pieLabels = [barYData[i] for i in range(0, min(len(barYData), numElemPieChart - 1))]
        pieLabels.append("Others")

        if statType == 'time':
            title = "Time usage statistics (" + selectedDate + ")" + " - " + totalPieValue
        else:
            title = "Keystrokes usage statistics (" + selectedDate + ")" + " - " + totalPieValue + " keystrokes"

        layout = html.Div([
            html.Center(html.H3(title)),
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
                            x = barXData,
                            y = barYData,
                            text = barTextData,
                            width = [0.5 for i in range(0, len(barXData))],
                            orientation = 'h',
                            hoverinfo='text',
                        )
                    ],
                    'layout': go.Layout(
                        xaxis = dict(
                            tickvals = barTickValues,
                            ticktext = barTickText
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