from dash import html
import dash_bootstrap_components as bootstrap
import __utilities__ as utilities

def build_page():
    functions = []

    for function in utilities.scrape_functions().values():
        jumbotron = bootstrap.Container(
            [
                html.H1(function["functionName"], className="display-5"),
                html.P(function["functionDescription"], className="lead"),
                html.Hr(className="my-2"),
                html.P(function["functionText"], className="small", style={"white-space": "pre-wrap"}),
            ],
            fluid=True,
            className="py-2",
        )
        functions.append(jumbotron)
    
    return bootstrap.Container(
        children=functions,
        fluid=True,
    )
