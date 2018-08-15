import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import csv
import datetime
import time
import tzlocal
import pytz
from pytz import timezone
from random import randint

import config
from app import app

def toUnixTime(dt):
    epoch =  datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000

def toBaseTime(base, dt):
    return (dt - base).total_seconds() * 1000    

def getTimelineLayout(fileName):
    xData = []
    yData = []
    textData = []
    colorData = []
    xRange = [None, None]
    baseData = []

    pathToFile = config.LOGS_DIR + config.TIMELINE_DIR + fileName

    with open(pathToFile, 'r') as csvFile:
        csvReader = csv.DictReader(csvFile)
        lc = 0

        # Read data and prepare it for visualization
        for row in csvReader:
            #if lc == 10:
            #    break

            start =  datetime.datetime.strptime(fileName + " " + row["start"], "%Y-%m-%d %H:%M:%S")
            finish = datetime.datetime.strptime(fileName + " " + row["finish"], "%Y-%m-%d %H:%M:%S")

            # We need to use the 'base' attribute of the axes in Plotly, since, when we
            # plot the dates, Plotly will, under the hood, compute the difference between
            # 1 January 1970 and the current date. So, we need to provide another 'base' for this,
            # and work with the difference between the date and that 'base' as our x_data.
            baseData.append([start])
            
            if lc == 0:
                xRange[0] = datetime.datetime.strptime(row["start"], "%H:%M:%S")

            xRange[1] = datetime.datetime.strptime(row["finish"], "%H:%M:%S")

            #x_data.append([1000])

            #currentTime = datetime.datetime.now()
            #currentUtcTime = currentTime.replace(tzinfo=timezone('UTC'))
            #timeZoneDiff = (currentTime - currentUtcTime).total_seconds() * 1000
            #print(timeZoneDiff)

            dummyDate = datetime.datetime(1970, 1, 1)
            dummyLocalTime = tzlocal.get_localzone().localize(dummyDate)
            dummyUtcTime = pytz.utc.localize(dummyDate)

            diffTime = toBaseTime(dummyLocalTime, dummyUtcTime)
            #print(xElem)
            #TODO: Open issue with numbers in range [1000, 9000]
            xData.append([toBaseTime(start, finish) - diffTime])
            #x_data.append([finish])

            yData.append([randint(1, 4)])
            #y_data.append([randint(1, 4)])
            #y_data.append([randint(1, 4)])
            textData.append([row["window"]])

            #text_data.append('Start time: ' + str(row["start"]) + \
            #        ', Finish time: ' + str(row["finish"]))
            color = (randint(0, 255), randint(0, 255), randint(0, 255))
            colorData.append(['rgb' + str(color)])
            lc += 1

        # print(x_data[0][0])

        # Return the layout with the correspondent data
        return html.Div([
            html.H1('Page 1'),
            html.Div(id='page-1-content'),
            dcc.Graph(
                figure=go.Figure(
                    data=[
                        go.Bar(
                            x=xElem,
                            y=[0],
                            base=baseElem,
                            width=yElem,
                            offset=[0],
                            text=textElem,
                            orientation='h',
                            name='',
                            marker=dict(
                                color=colorElem
                            )
                        )
                    for xElem, yElem, baseElem, colorElem, textElem in zip(xData, yData, baseData, colorData, textData)],
                    layout=go.Layout(
                        title='US Export of Plastic Scrap',
                        xaxis= dict(   
                            #range = [x_range[0],
                            #         x_range[1]],
                            #range = [toUnixTime(datetime.datetime(2013, 10, 17)),
                            #        toUnixTime(datetime.datetime(2013, 11, 20))],
                            type = 'date'
                        ),
                        yaxis=dict(rangemode='tozero',
                                    autorange=True),
                        showlegend=False,
                        barmode='stack',
                        hovermode='closest',
                        #legend=dict (
                        #    x=0,
                        #    y=1.0
                        #),
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