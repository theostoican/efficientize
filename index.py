import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import tracking_window

from app import app
from apps import app1

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# Callback that listens to the URL and provide the correspondent content
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-1':
        return app1.page_1_layout
    else:
        # Get all the days for which we have gathered data
        dates = tracking_window.get_available_days()
        # This is the index (a.k.a. main) page of the app
        index_page = html.Div([html.Div([dcc.Link(date, href='/page-1'), html.Br()]) for date in dates])

        return index_page

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})


if __name__ == '__main__':
    app.run_server(debug=True)