import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import csv
import datetime
import time
import tzlocal
import pytz
import os
from pytz import timezone
from random import randint

import config
from app import app

# Function to convert to Unix time
def toUnixTime(dt):
    epoch =  datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000

# Similarly to toUnixTime, this functions converts to the 'base' time, i.e.
# the number of seconds elapsed since a particular time
def toBaseTime(base, dt):
    return (dt - base).total_seconds() * 1000    

# Helper functions to determine the category in which a number of
# keystrokes fits. There are 4 categories shown in the chart:
#   -> LOW
#   -> MEDIUM
#   -> HIGH
#   -> STREAK
# keystrokesFreq represents the number of keystrokes/sec on average
def getKeystrokeCategory(keystrokesFreq):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    STREAK = 4

    if keystrokesFreq < 1:
        return LOW
    elif keystrokesFreq < 3:
        return MEDIUM
    elif keystrokesFreq < 4:
        return HIGH
    else:
        return STREAK

def getTimelineLayout(selectedDate):
    dateDir = config.LOGS_DIR + config.TIMELINE_DIR + selectedDate + '/'
    hourFiles = os.listdir(dateDir)

    if len(hourFiles) == 0:
        return 'There is no data available for this day.'
    # Return the layout with the correspondent data

    hourFiles.sort()
    
    return html.Div([
        html.H1('Page 1'),
        html.Div(id='page-1-content'),
        dcc.Dropdown(
            id='my-dropdown',
            options=[
                {'label': hourFile, 'value': hourFile}
                    for hourFile in hourFiles],
            value=hourFiles[-1]
        ),
        html.Div(children=selectedDate, id='date', style={'display': 'none'}),
        dcc.Graph(id='timeline'),
        html.Br(),
        dcc.Link('Go back to home', href='/'),
    ])


@app.callback(dash.dependencies.Output('timeline', 'figure'),
              [dash.dependencies.Input('my-dropdown', 'value'),
               dash.dependencies.Input('date', 'children')])
def page_1_dropdown(hourFile, selectedDate):
    xData = []
    yData = []
    widthData = []
    textData = []
    colorData = []
    xRange = [None, None]
    baseData = []
    dateDir = config.LOGS_DIR + config.TIMELINE_DIR + selectedDate + '/'
    pathToFile = dateDir + hourFile

    with open(pathToFile, 'r') as csvFile:
        csvReader = csv.DictReader(csvFile)
        lc = 0

        # Read data and prepare it for visualization
        for row in csvReader:
            #if lc == 3:
            #    break

            start =  datetime.datetime.strptime(selectedDate + " " + row["start"], "%Y-%m-%d %H:%M:%S")
            finish = datetime.datetime.strptime(selectedDate + " " + row["finish"], "%Y-%m-%d %H:%M:%S")

            # We need to use the 'base' attribute of the axes in Plotly, since, when we
            # plot the dates, Plotly will, under the hood, compute the difference between
            # 1 January 1970 and the current date and will draw a bar from there up to our date.
            # So, if we want to draw a bar from another date, we need to provide a 'base'
            # for this, and work with the difference between one date and that 'base' as 
            # our x_data.

            baseData.append([start])
            
            if lc == 0:
                xRange[0] = start

            xRange[1] = finish

            # There are two ways that we can use to provide Plotly with dates:
            #   -> via datetime
            #   -> via integers, representing the ellapsed seconds since the
            #       first event on the axis (the 'base')

            # Issue1 & Sol: If we provide datetime, Plotly will under the hood
            # compute  the offset since 1 Jan 1970 and will erroneously enlarge
            # the width of the bar. Hence, we must use integers, since they
            # will not be further processed.
            
            # Issue2 & Sol: If we provide integers, Plotly will convert
            # integers to the local time of the browser (adding or subtracting
            # hours from UTC time), without taking into account DST. Hence, we
            # subtract that same difference between the timezones from the
            # integer, by choosing one non-DST date, so that it will nullify
            # what Plotly will add.

            dummyDate = datetime.datetime(1970, 1, 1)
            dummyLocalTime = tzlocal.get_localzone().localize(dummyDate)
            dummyUtcTime = pytz.utc.localize(dummyDate)

            diffTime = toBaseTime(dummyLocalTime, dummyUtcTime)

            #TODO: Open issue with numbers in range [1000, 9000]
            xData.append([toBaseTime(start, finish) - diffTime])
            yData.append([0])

            keystrokesFreq = float(row["keystrokes"])

            widthData.append([getKeystrokeCategory(keystrokesFreq)])
            textData.append([start.strftime("%H:%M:%S") + ' - ' + \
                finish.strftime("%H:%M:%S") + '<br>' + row["window"] + \
                '<br>' + '{:.2f}'.format(keystrokesFreq) + ' keystrokes/s'])

            color = (randint(0, 255), randint(0, 255), randint(0, 255))
            colorData.append(['rgb' + str(color)])
            lc += 1
    return {
        'data':[
            go.Bar(
                x=xElem,
                y=yElem,
                base=baseElem,
                width=widthElem,
                offset=[0],
                text=textElem,
                orientation='h',
                name='',
                hoverinfo='text',
                marker=dict(
                    color=colorElem
                )
            )
        for xElem, yElem, widthElem, baseElem, colorElem, textElem in zip(xData, yData, widthData, baseData, colorData, textData)],
        'layout': go.Layout(
            title='Work and Pause Timeline',
            xaxis= dict(   
                #range = [xRange[0],
                #         xRange[0] + datetime.timedelta(minutes=25)],
                rangeslider=dict(
                    #id = 'timeline-slider',
                    visible = True
                ),
                type = 'date'
            ),
            yaxis=dict(
                tickvals = [1, 2, 3, 4],
                ticktext = ['Low', 'Medium', 'High', 'Streak'],
                position=0.025
            ),
            showlegend=False,
            barmode='stack',
            hovermode='closest',
            margin=dict(l=40, r=0, t=40, b=30)
        )
    }
                
