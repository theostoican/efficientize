import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from apps import app1, app2

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

index_page = html.Div([
    html.H2("Sample Analytics")
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    #print("Pathname: " + pathname)
    if pathname == '/apps/app1':
         return app1.layout
    elif pathname == '/': #if pathname == '/apps/app2':
         return index_page
    #elif pathname == '/':
    #    return app.layout
    else:
        #print(pathname)
    #    return app.layout

if __name__ == '__main__':
    app.run_server(debug=True)