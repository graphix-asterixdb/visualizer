import json
import dash
import pathlib
import requests
from dash import html
import dash_bootstrap_components as bootstrap
from __errors__ import *
from __global__ import *

class _MetadataPage:
    def __call__(self, *args, **kwargs):
        return ''

def get_metadata(dataverse, dataset):
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
    dash.Output({"dataverse": dash.ALL, "type": dash.ALL, "idx": dash.ALL}, 'n_clicks'),
    dash.Input({"dataverse": dash.ALL, "type": dash.ALL, "idx": dash.ALL}, 'n_clicks'),
    dash.State({"dataverse": dash.ALL, "type": dash.ALL, "idx": dash.ALL}, 'value'),
    prevent_initial_call=True,
)
def _update(n_clicks, data):
    for i in range(len(n_clicks)):
        if n_clicks[i]:
            return str(data[i]), [None for item in n_clicks]
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
                                            html.Div(bootstrap.Button(
                                                get_name(item),
                                                value=item,
                                                id={"dataverse": dataverse, "type": group_name, "idx": idx}
                                            )) for idx, item in enumerate(value)
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
            bootstrap.Col(html.P(id='choice'))
        ]
    )