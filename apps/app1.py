import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import tracking_window
from app import app

page_1_layout = html.Div([
    html.H1('Page 1'),
    html.Div(id='page-1-content'),
    dcc.Graph(
    figure=go.Figure(
        data=[
            go.Bar(
                x=[1995, 1996],
                y=[219, 146],
                name='Rest of world',
                marker=dict(
                    color=['rgb(55, 83, 109)', 'rgb(2, 240, 104)']
                )
            )
        ],
        layout=go.Layout(
            title='US Export of Plastic Scrap',
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