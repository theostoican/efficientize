import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import threading
import os

from pynput.keyboard import Key, Listener

from tracking_window import Tracker
from app import app
from apps import timeline_vis, statistics_vis
import config


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

tracker = Tracker()

def getAvailableDays():
    availDates = os.listdir(config.LOGS_DIR + config.TIMELINE_DIR)
    
    availDates.sort()
    
    return availDates

# Get the data from the available days which in stored on the disk
# when the server starts
days = getAvailableDays()

# Callback that listens to the URL and provide the correspondent content
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname is None:
        return ''
    elif pathname == '/':
        global days
        # Get all the days for which we have gathered data (we need
        # to read each time from the disk because new data might be stored
        # on disk while the server is running)
        days = getAvailableDays()

        daysHtmlList = [
            html.Li(
                [
                    dcc.Link(day, href = day),
                    dcc.Link(
                        [html.Button('View stats', style = {'verticalAlign' : 'middle',
                                                            'margin-left' : '2vw'})],
                        href='/stats/' + day,
                    ),
                ], 
        style = {'font-size':'2vw'}) 
        for day in days]

        # This is the index (a.k.a. main) page of the app
        index_page = html.Div([
            html.Center(html.H1("Available days")),
            html.Center(html.Ul(daysHtmlList))
        ])

        return index_page
    elif len(pathname) > 7 and pathname[:7] == '/stats/':
        # Remove the '/stats/' from the beginning of the pathname in order
        # to get the day
        day = pathname[7:]

        if day not in days:
            return '404'
        return statistics_vis.getTabsLayout(day)

    else:
        # Remove the '/' from the beginning of the pathname in order
        # to get the day
        day = pathname[1:]

        if day in days:
            return timeline_vis.getTimelineLayout(day)
        return '404'

if __name__ == '__main__':
    app.run_server()