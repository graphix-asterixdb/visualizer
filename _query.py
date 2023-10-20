import math

import visdcc
import pandas
import flatten_json
import dash.html as html
import dash_ace
import dash
import requests
import typing
import pathlib
import json
import re
import math
import diskcache

import dash_bootstrap_components as bootstrap
import dash_loading_spinners as spinners
import __utilities__ as utilities
from __global__ import *
from __errors__ import *

_callback_manager = dash.DiskcacheManager(diskcache.Cache())

@app.callback(
    dash.Output('queryResults', 'data'),
    dash.Input('runButton', 'n_clicks'),
    dash.State('queryInput', 'value'),
    prevent_initial_call=True,
    manager=_callback_manager,
    background=True,
    running=[
        (dash.Output('runButton', 'disabled'), True, False),
        (dash.Output('outputPaneSpinner', 'children'), spinners.Grid(color='#325d88'), None)
    ]
)
def _execute_query(n_clicks, query_input):
    settings_file = pathlib.Path(__file__).parent / 'settings/graphix.json'
    if not settings_file.exists():
        raise FileNotFoundError(settings_file.name)

    # Don't proceed if our query-text is empty.
    if query_input is None or (query_input is str and len(query_input) == 0) or n_clicks < 1:
        raise dash.exceptions.PreventUpdate

    # Grab our client information.
    with settings_file.open('r') as fp:
        settings_json = json.load(fp)
        cluster_uri = f"http://{settings_json['cluster']['address']}:" \
                      f"{settings_json['cluster']['port']}/query/service"

    # Issue our query.
    api_parameters = {'statement': 'SET `graphix.compiler.add-context` "true"; ' + query_input}
    response = requests.post(cluster_uri, api_parameters).json()
    if response['status'] != 'success':
        raise GraphixStatementError(response)
    return response['results']

@app.callback(
    dash.Output('tableViewer', 'data'),
    dash.Output('tableViewer', 'columns'),
    dash.Input('queryResults', 'data'),
    dash.Input('outputTabs', 'active_tab')
)
def _update_table(query_results, active_tab):
    if active_tab != 'tableOutputTab':
        raise dash.exceptions.PreventUpdate

    # Our results need to be flattened for use in a table.
    table_data = [flatten_json.flatten(x) for x in query_results]
    column_names = set(k for kk in [x.keys() for x in table_data] for k in kk)
    table_columns = [{"name": i, "id": i} for i in column_names]
    return table_data, table_columns

def build_page():
    def _build_input_pane():
        return bootstrap.Card(
            className='vh-100',
            children=[
                bootstrap.CardBody(
                    children=[
                        dash_ace.DashAceEditor(
                            id='queryInput',
                            mode=None,
                            theme='textmate',
                            placeholder=None,
                            showGutter=True,
                            showPrintMargin=False,
                            maxLines=math.inf,
                            syntaxKeywords={
                                'support.function': '|'.join(x for x in utilities.scrape_functions().keys()),
                                'keyword.other': '|'.join(x for x in utilities.scrape_keywords()),
                                'constant.language': 'true|false'
                            },
                            className='h-100 w-100'
                        ),
                        html.Div(
                            className='position-relative',
                            children=[
                                html.Button(
                                    id='runButton',
                                    className='btn btn-primary position-absolute bottom-0 end-0 queryButton',
                                    children=[
                                        html.Span(className="bi bi-play", style={'font-size': '16px'}),
                                        " Run "
                                    ],
                                    type='button',
                                    n_clicks=0
                                )
                            ]
                        )
                    ]
                )
            ]
        )

    def _build_output_pane():
        return bootstrap.Card(
            id='outputPane',
            className='vh-100',
            children=[
                bootstrap.CardBody(
                    className='position-relative',
                    children=[
                        bootstrap.Tabs(
                            id='outputTabs',
                            children=[
                                bootstrap.Tab(
                                    tab_id='graphOutputTab',
                                    children=[
                                        visdcc.Network(
                                            id='graphViewer',
                                            data={'nodes': [], 'edges': []},
                                            options={
                                                'width': '100%',
                                                'height': '100%'
                                            }
                                        )],
                                    label="Graph Viewer",
                                ),
                                bootstrap.Tab(
                                    tab_id='tableOutputTab',
                                    children=[
                                        dash.dash_table.DataTable(
                                            id='tableViewer',
                                            # style_table={
                                            #     'width': '100%',
                                            #     'height': '100%'
                                            # }
                                        )
                                    ],
                                    label="Table Viewer",
                                )
                            ]
                        ),
                        html.Div(
                            id='outputPaneSpinner',
                            className='position-absolute top-50 start-50 translate-middle',
                        )
                    ]
                )
            ]
        )

    return bootstrap.Container(
        children=[
            bootstrap.Row(
                children=[
                    bootstrap.Col(_build_input_pane(), width=6),
                    bootstrap.Col(_build_output_pane(), width=6)
                ],
                className="g-2",
            )
        ],
        fluid=True
    )
