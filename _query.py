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
from _metadata import get_metadata

_callback_manager = dash.DiskcacheManager(diskcache.Cache())


@app.callback(
    dash.Output('net', 'options'),
    dash.Input('graphSettings', 'data'),
)
def _load_graph_settings(settings):
    print(settings)
    return settings

@app.callback(
    dash.Output('graphSettings', 'data'),
    dash.Input('url', 'pathname'),
    dash.State('graphSettings', 'data'),
)
def _load_node_labels(pathname, settings):
    if pathname != QUERY_DIRECTORY:
        raise dash.exceptions.PreventUpdate

    if 'groups' not in settings:
        settings['groups'] = {}
    color_map = settings['groups']
    graphs = get_metadata('Metadata', 'Graph')
    for graph in graphs:
        for node in graph['Vertices']:
            if node['Label'] not in color_map:
                color_map[node['Label']] = {
                    'borderWidth': 0,
                    'color': {'background': '#97C2FC'},
                }
    return settings

@app.callback(
    dash.Output('queryResults', 'data'),
    dash.Output('graphData', 'data'),
    dash.Input('runButton', 'n_clicks'),
    dash.State('queryInput', 'value'),
    dash.State('node-limit', 'data'),
    prevent_initial_call=True,
    manager=_callback_manager,
    background=True,
    running=[
        (dash.Output('runButton', 'disabled'), True, False),
        (dash.Output('outputPaneSpinner', 'children'), spinners.Grid(color='#325d88'), None),
        (dash.Output('net', 'style'), {'display': 'none'}, {'display': 'block'})
    ]
)
def _execute_query(n_clicks, query_input, node_limit):
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
            if idx >= node_limit:
                break
            if variable in node_variables:
                node_tuple = dict_to_tuple(node)
                if node_tuple in nodes:
                    id_dict[variable] = nodes[node_tuple]["id"]
                else:
                    idx += 1
                    id_dict[variable] = idx
                    label = node['name'] if 'name' in node else f"{node_variables[variable]}-{idx}"
                    title_json = json.dumps(node, indent=2)
                    nodes[node_tuple] = {
                        "id": idx,
                        "data": node,
                        "label": "\n".join(label.split()),
                        "group": node_variables[variable],
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
    dash.Output('outputTabs', 'active_tab'),
    dash.Input('graphData', 'data'),
    dash.Input('outputTabs', 'active_tab')
)
def _update_graph(graph_data, active_tab):
    if active_tab != 'graphOutputTab':
        raise dash.exceptions.PreventUpdate
    
    if not graph_data['nodes']:
        print('Cannot show data as graph, switch to Table Viewer tab...')
        return graph_data, 'tableOutputTab'
    
    return graph_data, 'graphOutputTab'

@app.callback(
    dash.Output('queryInput', 'theme'),
    dash.Output('tableViewer', 'style_header'),
    dash.Output('tableViewer', 'style_data'),
    dash.Output('tableViewer', 'style_data_conditional'),
    dash.Input(ThemeSwitchAIO.ids.switch('theme'), 'value')
)
def _update_theme(is_light):
    if is_light:
        query_input_theme = 'textmate'
        style_header = {
            'backgroundColor': 'rgb(220, 220, 220)',
            'color': 'black',
            'fontWeight': 'bold'
        }
        style_data = {
            'color': 'black',
            'backgroundColor': 'white'
        }
        style_data_conditional = [
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(240, 240, 240)',
            }
        ]
    else:
        query_input_theme = 'twilight'
        style_header = {
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white',
            'fontWeight': 'bold'
        }
        style_data = {
            'backgroundColor': 'rgb(70, 70, 70)',
            'color': 'white'
        }
        style_data_conditional = [
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(50, 50, 50)',
            }
        ]
    return query_input_theme, style_header, style_data, style_data_conditional


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
                                            id='net',
                                            data={
                                                'nodes': [
                                                    {'id': 1},
                                                    {'id': 2},
                                                ],
                                                'edges': [
                                                    {'from': 1, 'to': 2},
                                                ],
                                            },
                                            options={
                                                'height': '600px',
                                                'width': '100%',
                                            }
                                        ),
                                    ],
                                    label="Graph Viewer",
                                ),
                                bootstrap.Tab(
                                    tab_id='tableOutputTab',
                                    children=[
                                        dash.dash_table.DataTable(
                                            id='tableViewer',
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
