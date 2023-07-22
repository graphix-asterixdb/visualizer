import dash.html as html
from __global__ import *

import dash_bootstrap_components as bootstrap
import _query as query_page
import _functions as functions_page
import _metadata as metadata_page
import _settings as settings_page

app.layout = html.Div(
    children=[
        dash.dcc.Location(id="url"),
        dash.dcc.Store(id='queryResults'),
        bootstrap.Col(
            className='mainSidebar bg-light',
            children=[
                html.Img(src=app.get_asset_url('logo.svg'), width='100%'),
                html.Hr(),
                bootstrap.Nav(
                    children=[
                        bootstrap.NavLink("Query Browser", href=QUERY_DIRECTORY, active="exact"),
                        bootstrap.NavLink("Metadata Browser", href=METADATA_DIRECTORY, active="exact"),
                        bootstrap.NavLink("Built-In Functions", href=FUNCTIONS_DIRECTORY, active="exact"),
                        bootstrap.NavLink("Client Settings", href=SETTINGS_DIRECTORY, active="exact"),
                        bootstrap.DropdownMenu(
                            children=[
                                bootstrap.DropdownMenuItem(
                                    "Graphix Website",
                                    href="https://graphix.ics.uci.edu",
                                    target="_blank",
                                ),
                                bootstrap.DropdownMenuItem(
                                    "AsterixDB Website",
                                    href="https://asterixdb.apache.org",
                                    target="_blank",
                                ),
                                bootstrap.DropdownMenuItem(
                                    "AsterixDB Documentation",
                                    href="https://nightlies.apache.org/asterixdb/index.html",
                                    target="_blank",
                                )
                            ],
                            nav=True,
                            in_navbar=True,
                            label="External Links"
                        )
                    ],
                    vertical=True,
                    pills=True
                )
            ]
        ),
        html.Div(id="page-content", className='mainContent'),
    ]
)

# Define our callback for our page content.
@app.callback(
    dash.Output("page-content", "children"),
    dash.Input("url", "pathname")
)
def render_page_content(pathname):
    if pathname == QUERY_DIRECTORY:
        return query_page.build_page()
    elif pathname == METADATA_DIRECTORY:
        return metadata_page.build_page()
    elif pathname == FUNCTIONS_DIRECTORY:
        return functions_page.build_page()
    elif pathname == SETTINGS_DIRECTORY:
        return settings_page.build_page()
    else:  # TODO (GLENN): Make a 404 page?
        pass

if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_hot_reload=False)
