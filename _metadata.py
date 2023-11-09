import json
import dash
import pathlib
import requests
from dash import html, dcc
import dash_loading_spinners as spinners
import dash_bootstrap_components as bootstrap
from __errors__ import *
from __global__ import *

class _MetadataPage:
    def __call__(self, *args, **kwargs):
        return ''

def get_metadata(dataverse, dataset, limit=None):
    settings_file = pathlib.Path(__file__).parent / 'settings/graphix.json'
    if not settings_file.exists():
        raise FileNotFoundError(settings_file.name)
    
    # Grab our client information.
    with settings_file.open('r') as fp:
        settings_json = json.load(fp)
        cluster_uri = f"http://{settings_json['cluster']['address']}:" \
                      f"{settings_json['cluster']['port']}/query/service"
    
    # Issue our query.
    query_str = f"use `{dataverse}`; select value d from `{dataset}` d;"
    if limit is not None:
        query_str = f"use `{dataverse}`; select value d from `{dataset}` d limit {limit};"
    api_parameters = {'statement': 'SET `graphix.compiler.add-context` "true"; ' + query_str}
    response = requests.post(cluster_uri, api_parameters).json()
    if response['status'] != 'success':
        raise GraphixStatementError(response)
    return response['results']

def get_name(item):
    attribute_name_list = ["DatasetName", "DatatypeName", "GraphName"]
    for attribute_name in attribute_name_list:
        if item.get(attribute_name):
            return item.get(attribute_name)
    return "UNDEFINED"


@app.callback(
    dash.Output('choice', 'children'),
    dash.Output({"dataverse": dash.ALL, "type": "Dataset", "idx": dash.ALL}, 'n_clicks'),
    dash.Input({"dataverse": dash.ALL, "type": "Dataset", "idx": dash.ALL}, 'n_clicks'),
    dash.State({"dataverse": dash.ALL, "type": "Dataset", "idx": dash.ALL}, 'data-detail'),
    prevent_initial_call=True,
    running=[(dash.Output('detail-spinner', 'children'), spinners.Grid(color='#325d88'), None)]
)
def _dataset_detail(n_clicks, data):
    for i in range(len(n_clicks)):
        if n_clicks[i]:
            detail = data[i]
            sample = get_metadata(detail["DataverseName"], detail["DatasetName"], 1)
            jumbotron = bootstrap.Container(
                [
                    html.H1("Dataset: " + detail["DatasetName"], className="display-5"),
                    html.Br(),
                    html.Hr(className="my-2"),
                    html.Br(),
                    html.P("Dataverse: " + detail["DataverseName"]),
                    html.P("Dataset: " + detail["DatasetName"]),
                    html.P("Datatype: " + detail["DatatypeName"]),
                    html.P("Primary Keys:"),
                    html.Ul([html.Li(pk[0]) for pk in detail["InternalDetails"]["PrimaryKey"]]),
                    html.P("Sample:"),
                    bootstrap.Container(html.Pre(html.Code(json.dumps(sample, indent=2))), className="code"),
                ],
                fluid=True,
                className="py-2",
            )
            return jumbotron, [None for item in n_clicks]
    return None, [None for item in n_clicks]

@app.callback(
    dash.Output('choice', 'children', allow_duplicate=True),
    dash.Output({"dataverse": dash.ALL, "type": "Datatype", "idx": dash.ALL}, 'n_clicks'),
    dash.Input({"dataverse": dash.ALL, "type": "Datatype", "idx": dash.ALL}, 'n_clicks'),
    dash.State({"dataverse": dash.ALL, "type": "Datatype", "idx": dash.ALL}, 'data-detail'),
    prevent_initial_call=True,
    running=[(dash.Output('detail-spinner', 'children'), spinners.Grid(color='#325d88'), None)]
)
def _datatype_detail(n_clicks, data):
    for i in range(len(n_clicks)):
        if n_clicks[i]:
            detail = data[i]
            try:
                fields = detail["Derived"]["Record"]["Fields"]
            except KeyError:
                fields = []
            jumbotron = bootstrap.Container(
                [
                    html.H1("Datatype: " + detail["DatatypeName"], className="display-5"),
                    html.Br(),
                    html.Hr(className="my-2"),
                    html.Br(),
                    html.P("Dataverse: " + detail["DataverseName"]),
                    html.P("Datatype: " + detail["DatatypeName"]),
                    html.P("Fields:"),
                    bootstrap.Container(
                        [html.P([
                            f"{field['FieldName']} ({field['FieldType']})",
                            html.Span(f"{'Nullable' if field['IsNullable'] else 'Not Nullable'} | "
                                f"{'Not Required' if field['IsMissable'] else 'Required'}", style={"float": "right"})
                        ]) for field in fields]
                    ),
                ],
                fluid=True,
                className="py-2",
            )
            return jumbotron, [None for item in n_clicks]
    return None, [None for item in n_clicks]

@app.callback(
    dash.Output('choice', 'children', allow_duplicate=True),
    dash.Output({"dataverse": dash.ALL, "type": "Graph", "idx": dash.ALL}, 'n_clicks'),
    dash.Input({"dataverse": dash.ALL, "type": "Graph", "idx": dash.ALL}, 'n_clicks'),
    dash.State({"dataverse": dash.ALL, "type": "Graph", "idx": dash.ALL}, 'data-detail'),
    prevent_initial_call=True,
    running=[(dash.Output('detail-spinner', 'children'), spinners.Grid(color='#325d88'), None)]
)
def _graph_detail(n_clicks, data):
    for i in range(len(n_clicks)):
        if n_clicks[i]:
            detail = data[i]
            jumbotron = bootstrap.Container(
                [
                    html.H1("Graph: " + detail["GraphName"], className="display-5"),
                    html.Br(),
                    html.Hr(className="my-2"),
                    html.Br(),
                    html.P("Dataverse: " + detail["DataverseName"]),
                    html.P("Graph: " + detail["GraphName"]),
                    html.P("Vertices:"),
                    bootstrap.Container(
                        html.Pre(html.Code(json.dumps(detail["Vertices"], indent=2))),
                        className="code"
                    ),
                    html.Br(),
                    html.P("Edges:"),
                    bootstrap.Container(
                        html.Pre(html.Code(json.dumps(detail["Edges"], indent=2))),
                        className="code"
                    ),
                ],
                fluid=True,
                className="py-2",
            )
            return jumbotron, [None for item in n_clicks]
    return None, [None for item in n_clicks]


def build_page():
    metadata_dict = {}
    metadata_type_list = ["Dataset", "Datatype", "Graph"]

    for dataverse in get_metadata("Metadata", "Dataverse"):
        metadata_dict[dataverse['DataverseName']] = {"Dataset": [], "Datatype": [], "Graph": []}

    for metadata_type in metadata_type_list:
        for metadata in get_metadata("Metadata", metadata_type):
            dataverse_name = metadata["DataverseName"]
            metadata_dict[dataverse_name][metadata_type].append(metadata)

    return bootstrap.Row(
        [
            bootstrap.Col(
                bootstrap.Accordion(
                    [
                        bootstrap.AccordionItem(
                            bootstrap.Accordion(
                                [
                                    bootstrap.AccordionItem(
                                        [
                                            html.Div(
                                                get_name(item),
                                                **{"data-detail": item},
                                                className="metadata-list-item",
                                                id={"dataverse": dataverse, "type": group_name, "idx": idx}
                                            ) for idx, item in enumerate(value)
                                        ],
                                        title=group_name,
                                    ) for group_name, value in groups.items()
                                ]
                            ),
                            title=dataverse,
                        ) for dataverse, groups in metadata_dict.items()
                    ],
                ),
                width=4
            ), 
            bootstrap.Col(
                [
                    html.Div(id='choice'),
                    html.Div(id='detail-spinner', className='position-absolute top-50 start-50 translate-middle')
                ],
                width=8
            )
        ]
    )