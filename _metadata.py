import json
import pathlib
import requests
from dash import html
import dash_bootstrap_components as bootstrap
from __errors__ import *

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

def build_page():
    dataverse_list = [html.P("Dataverses:")]
    for dataverse in get_metadata("Metadata", "Dataverse"):
        dataverse_list.append(html.P(dataverse['DataverseName']))
    return bootstrap.Container(children=dataverse_list, fluid=True)