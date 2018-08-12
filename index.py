import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from tracking_window import Tracker

from app import app
from apps import app1
import config

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

tracker = Tracker()

# Get the data from the available days which in stored on the disk
# when the server starts
days = tracker.getAvailableDays()

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
        days = tracker.getAvailableDays()
        # This is the index (a.k.a. main) page of the app
        index_page = html.Div([html.Div([dcc.Link(day, href=day), html.Br()]) for day in days])

        return index_page
    else: #pathname is not None:
        # Remove the '/' from the beginning of the pathname in order
        # to get the day
        day = pathname[1:]

        if day in days:
            return app1.page_1_layout
        return '404'

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


if __name__ == '__main__':
    app.run_server(debug=True)