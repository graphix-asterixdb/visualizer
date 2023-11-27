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

from dash_bootstrap_templates import ThemeSwitchAIO
import dash_bootstrap_components as bootstrap
import dash_loading_spinners as spinners
import __utilities__ as utilities
from __global__ import *
from __errors__ import *

_callback_manager = dash.DiskcacheManager(diskcache.Cache())


@app.callback(
    dash.Output('queryResults', 'data'),
    dash.Output('graphData', 'data'),
    dash.Input('runButton', 'n_clicks'),
    dash.State('queryInput', 'value'),
    prevent_initial_call=True,
    manager=_callback_manager,
    background=True,
    running=[
        (dash.Output('runButton', 'disabled'), True, False),
        (dash.Output('outputPaneSpinner', 'children'), spinners.Grid(color='#325d88'), None),
        (dash.Output('net', 'style'), {'display': 'none'}, {'display': 'block'})
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
    if not response.get('results'):
        return {}, {'nodes': [], 'edges': []}
    
    # Store variable names representing nodes and edges.
    node_variables = {
        node["graphElement"]["variable"]: node["graphElement"]["labels"][0] 
        for node in response["graphix"]["patterns"]["vertices"]
    }
    edge_variables = {
        edge["graphElement"]["variable"]: {
            "label": edge["graphElement"]["labels"][0], 
            "from": edge["edgeElement"]["leftVertex"]["variable"], 
            "to": edge["edgeElement"]["rightVertex"]["variable"]
        } 
        for edge in response["graphix"]["patterns"]["edges"]
    }

    # Turn query result into nodes and edges.
    idx = 0
    nodes = {}
    edges = []
    for entry in response['results']:
        # Go through each node, cache each node's id.
        id_dict = {}
        for variable, node in entry.items():
            if variable in node_variables:
                node_tuple = dict_to_tuple(node)
                if node_tuple in nodes:
                    id_dict[variable] = nodes[node_tuple]["id"]
                else:
                    idx += 1
                    id_dict[variable] = idx
                    label = f"{node_variables[variable]} {idx}"
                    title_json = json.dumps(node, indent=2)
                    nodes[node_tuple] = {
                        "id": idx,
                        "data": node,
                        "label": label,
                        "title": f"<pre><code>{title_json}</code></pre>"
                    }
        # Go through each edge.
        for variable, edge in entry.items():
            if variable in edge_variables:
                edge_definition = edge_variables[variable]
                label = edge_definition["label"]
                if edge_definition["from"] not in id_dict or edge_definition["to"] not in id_dict:
                    continue
                title_json = json.dumps(edge, indent=2)
                edges.append({
                    "from": id_dict[edge_definition["from"]],
                    "to": id_dict[edge_definition["to"]],
                    "data": edge,
                    "label": label,
                    "title": f"<pre><code>{title_json}</code></pre>"
                })

    print({'nodes': list(nodes.values()), 'edges': edges})
    return response['results'], {'nodes': list(nodes.values()), 'edges': edges}

def dict_to_tuple(d):
    res = []
    for key, value in d.items():
        res.append(key)
        res.append(value)
    return tuple(res)

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

@app.callback(
    dash.Output('net', 'data'),
    dash.Input('graphData', 'data'),
    dash.Input('outputTabs', 'active_tab')
)
def _update_graph(graph_data, active_tab):
    if active_tab != 'graphOutputTab':
        raise dash.exceptions.PreventUpdate
    
    return graph_data

@app.callback(
    dash.Output('queryInput', 'theme'),
    dash.Output('tableViewer', 'style_header'),
    dash.Output('tableViewer', 'style_data'),
    dash.Input(ThemeSwitchAIO.ids.switch('theme'), 'value')
)
def _update_theme(is_light):
    if is_light:
        query_input_theme = 'textmate'
        style_header = {
            'backgroundColor': 'rgb(210, 210, 210)',
            'color': 'black',
            'fontWeight': 'bold'
        }
        style_data = {
            'color': 'black',
            'backgroundColor': 'white'
        }
    else:
        query_input_theme = 'twilight'
        style_header = {
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white',
            'fontWeight': 'bold'
        }
        style_data = {
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white'
        }
    return query_input_theme, style_header, style_data

@app.callback(
    dash.Output('net', 'data', allow_duplicate=True),
    dash.Input('testGraph', 'n_clicks'),
    prevent_initial_call=True
)
def _update_graph_test(n_clicks):
    return {
        'nodes': [
            {'id': 1, 'label': 'Node 1', 'title': 'test title'},
            {'id': 2, 'label': 'Node 2'},
        ],
        'edges': [
            {'from': 1, 'to': 2, 'label': '1 to 2', 'title': 'title'},
        ],
    }

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
                            value='FROM GRAPH Gelp.GelpGraph\n\t(r:Review)-[a:ABOUT]->(b:Business)\nSELECT r, a, b;',
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
                                ),
                                html.Button(
                                    id='testGraph',
                                    className='btn btn-primary position-absolute bottom-0 end-50 queryButton',
                                    children=[
                                        html.Span(className="bi bi-play", style={'font-size': '16px'}),
                                        " Test "
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
                                            id = 'net',
                                            data = {
                                                'nodes': [
                                                    {'id': 1, 'color': 'white'},
                                                    {'id': 2, 'color': 'white'},
                                                ],
                                                'edges': [
                                                    {'from': 1, 'to': 2},
                                                ],
                                            },
                                            options = {
                                                'autoResize': True,
                                                'height': '600px',
                                                'width': '100%',
                                                'edges': {
                                                    'arrows': {
                                                        'to': {
                                                            'enabled': True,
                                                            'scaleFactor': 1,
                                                            'type': "arrow",
                                                        }
                                                    },
                                                    'smooth': False,
                                                    'font': {
                                                        'align': 'middle',
                                                    },
                                                },
                                                'nodes': {
                                                    'shape': 'circle',
                                                    'color': {
                                                        'background': '#97C2FC',
                                                        'hover': {
                                                            'background': '#2B7CE9',
                                                        }
                                                    },
                                                },
                                                'interaction': {
                                                    'hover': True,
                                                    'hoverConnectedEdges': False,
                                                    'tooltipDelay': 50
                                                }
                                            }
                                        ),
                                        # html.Iframe(srcDoc=open('assets/graph.html', 'r').read(), width='100%', height='600')
                                    ],
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
