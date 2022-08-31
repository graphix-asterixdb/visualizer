import argparse
import graphviz
import os
import requests
import functools
import datetime
import configparser
import typing
import tabulate


def _to_response(input_string: str, **kwargs) -> requests.Response:
    """ Read in a query string, issue the query to a Graphix instance, and return a list of JSON documents. """
    cc_uri = kwargs['asterixdb']['address'] + ':' + kwargs['asterixdb']['port']
    cc_uri = 'http://' + cc_uri + '/query/service'
    return requests.post(cc_uri, {'statement': input_string}, timeout=int(kwargs['asterixdb']['timeout']))


def _to_json(input_response: requests.Response, **_) -> typing.List[typing.List[dict]]:
    """ Read in an list of JSON objects from a Graphix response and return a two-level list of Graphix path objects. """
    input_response_json = input_response.json()
    if input_response.status_code != 200 or 'results' not in input_response_json:
        raise RuntimeWarning(f'Could not retrieve results from server: {input_response_json}')

    if len(input_response_json['results']) == 0:
        raise RuntimeWarning('No results returned from the query.')

    path_objects = []
    for document in input_response_json['results']:
        if type(document) != dict:
            continue

        # We are looking for the following: [ { "Vertices": [{...}], "Edges": [{...}] }, ... ]
        if 'Vertices' in document and 'Edges' in document:
            if all(type(b) == dict for b in document['Vertices']) and all(type(b) == dict for b in document['Edges']):
                path_objects.append([document])

        # ...or the following: [ { "...": { "Vertices": [{...}], "Edges": [{...}] } }, ... ]
        path_objects_list = []
        for k, v in document.items():
            if type(v) != dict:
                continue
            if 'Vertices' not in v or 'Edges' not in v:
                continue
            if any(type(b) != dict for b in v['Vertices']) or any(type(b) != dict for b in v['Edges']):
                continue

            # We have found a path document.
            path_objects_list.append(v)
        path_objects.append(path_objects_list)

    return path_objects


def _to_dot(input_list: typing.List[typing.List[dict]], **kwargs) -> typing.List[graphviz.Digraph]:
    """ Read in a two-level list of Graphix path objects and return a list of DOT objects. """
    attribute_parser = lambda a: {} if len(a[0]) < 2 else {n.split('=')[0].strip(): n.split('=')[1].strip() for n in a}
    node_attributes = attribute_parser(kwargs['graphviz']['node-attributes'].split(' '))
    edge_attributes = attribute_parser(kwargs['graphviz']['edge-attributes'].split(' '))
    graph_attributes = attribute_parser(kwargs['graphviz']['graph-attributes'].split(' '))

    dot = graphviz.Digraph(comment=kwargs['file_prefix'],
                           graph_attr=graph_attributes, node_attr=node_attributes, edge_attr=edge_attributes)
    for path_doc_list in input_list:
        for path_doc in path_doc_list:
            dot_node_builder = lambda d: {'label': d['_GraphixSchemaDetail']['ElementLabel'],
                                          'key': d['_GraphixSchemaDetail']['VertexDetail']['VertexKey']}

            # Build our vertices (we need this in case we have dangling vertices).
            val_flattener = lambda s: {k: str(v) for k, v in s.items()}
            pretty_printer = lambda s: tabulate.tabulate(
                # [list(v for k, v in val_flattener(s).items())], tablefmt='html'
                list(zip(*val_flattener(s).items())), tablefmt='html'
            ).replace('<tbody>', '').replace('</tbody>', '') \
                .replace('style="text-align: right;"', '') \
                .replace('\n\n', '\n')
            for vertex in path_doc['Vertices']:
                if kwargs['graphviz']['node-labels'] == 'true':
                    label = '<' + pretty_printer(dot_node_builder(vertex)) + '>'
                else:
                    label = None
                dot.node(name=val_flattener(dot_node_builder(vertex))['key'], label=label)

            # Build our edges.
            for edge in path_doc['Edges']:
                dot_edge_dict = {
                    'label': edge['_GraphixSchemaDetail']['ElementLabel'],
                    'source-key': edge['_GraphixSchemaDetail']['EdgeDetail']['SourceKey'],
                    'dest-key': edge['_GraphixSchemaDetail']['EdgeDetail']['DestinationKey']
                }
                source_vertex = val_flattener(dot_node_builder(edge['_GraphixSchemaDetail']['EdgeSourceVertex']))['key']
                dest_vertex = val_flattener(dot_node_builder(edge['_GraphixSchemaDetail']['EdgeDestVertex']))['key']
                if kwargs['graphviz']['edge-labels'] == 'true':
                    label = dot_edge_dict['label']
                else:
                    label = None
                dot.edge(source_vertex, dest_vertex, label=label)

    return [dot]


def _to_image(input_dots: typing.List[graphviz.Digraph], **kwargs) -> None:
    image_output = kwargs['graphviz']['image-output']
    image_format = kwargs['graphviz']['image-format']
    file_prefix = kwargs['file_prefix']
    if not os.path.exists(image_output):
        os.mkdir(image_output)
    for i, input_dot in enumerate(input_dots):
        input_dot.render(
            filename=image_output + '/' + file_prefix + f'_{i}.gv',
            outfile=image_output + '/' + file_prefix + f'_{i}.{image_format}',
            engine=kwargs['graphviz']['layout-engine'], format=image_format, view=kwargs['show']
        )
        del input_dot


def main():
    file_type = argparse.FileType('r')
    parser = argparse.ArgumentParser(description='Visualize results from Graphix using Graphviz.')
    parser.formatter_class = functools.partial(argparse.HelpFormatter, max_help_position=60)
    parser._optionals.title = 'arguments'
    parser.add_argument('-c', '--config', type=file_type, default='visualize.ini', help='config for this visualizer')
    parser.add_argument('-s', '--show', type=bool, default=True, help='flag to immediately display the rendered graph')
    parser.add_argument('-f', '--file-prefix', type=str, help='name of the file to write to',
                        default=datetime.datetime.now().strftime('%m_%d_%Y_%H_%M_%S'))

    # We need exactly one of the options below specified.
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-q', '--query', type=str, help='query string to issue to the Graphix server')
    group.add_argument('-qf', '--query-file', type=file_type, help='query file to issue to the Graphix server')
    group.add_argument('-j', '--json', type=str, help='json(L) output string to directly visualize')
    group.add_argument('-jf', '--json-file', type=file_type, help='json(L) output file to directly visualize')
    arguments = vars(parser.parse_args())

    # Read in our configuration file as a dictionary.
    config_parser = configparser.ConfigParser()
    config_parser.read_file(arguments['config'])
    config = {s: dict(config_parser.items(s)) for s in config_parser.sections()}
    config['show'] = arguments['show']
    config['file_prefix'] = arguments['file_prefix']

    # Execute our visualization.
    compose = lambda *funcs: functools.reduce(lambda f, g: lambda x: f(g(x)), funcs, lambda x: x)
    config_wrapper = lambda f: lambda x: f(x, **config)
    action_dict = {
        'query': [_to_response, _to_json, _to_dot, _to_image],
        'query_file': [lambda f, **_: f.read(), _to_response, _to_json, _to_dot, _to_image],
        'json': [_to_dot, _to_image],
        'json_file': [lambda f, **_: f.read(), _to_dot, _to_image]
    }
    for option, arg in [(k, v) for k, v in arguments.items() if k in action_dict.keys() and v is not None]:
        compose(*(config_wrapper(f) for f in action_dict[option][::-1]))(arg)


if __name__ == '__main__':
    main()
