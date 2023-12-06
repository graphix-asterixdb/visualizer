from dash import html
import dash_bootstrap_components as bootstrap
import __utilities__ as utilities


def build_page():
    table_of_contents = []
    body = []

    for function_class, function_list in utilities.scrape_functions().items():
        table_of_contents.append(html.Li(html.A(function_class, href=f"#{function_class}")))
        body.append(html.Br())
        body.append(html.Br())
        body.append(html.A(html.H2(function_class), id=function_class))
        body.append(html.Br())

        for function in function_list:
            jumbotron = bootstrap.Container(
                [
                    html.H1(function["functionName"], className="display-6"),
                    html.P(function["functionDescription"], className="lead"),
                    html.Hr(className="my-2"),
                    html.P(function["functionText"], className="small", style={"white-space": "pre-wrap"}),
                ],
                fluid=True,
                className="py-2",
            )
            body.append(jumbotron)

    body = [html.H1("Builtin Functions"), html.Br(), html.H2("Table of Contents"), html.Ul(table_of_contents)] + body
    
    return bootstrap.Container(
        children=body,
        fluid=True,
    )
