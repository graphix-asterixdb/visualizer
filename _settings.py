import dash
from dash import html, ctx
import dash_daq as daq
import dash_bootstrap_components as bootstrap
from __errors__ import *
from __global__ import *


@app.callback(
    dash.Output('color-map', 'children'),
    dash.Input('graphSettings', 'data')
)
def _color_setting(settings):
    if settings is None:
        raise dash.exceptions.PreventUpdate
    else:
        return bootstrap.ListGroup(
            [
                bootstrap.ListGroupItem(
                    [
                        html.Div(k, style={'float': 'left'}),
                        html.Div(style={
                            'height': 16,
                            'width': 20,
                            'float': 'right',
                            'margin': 4,
                            'background': v['color']['background']
                        }),
                    ],
                    id={'group-name': k}
                )
                for k, v in settings['groups'].items()
            ]
        )

@app.callback(
    dash.Output('group-choice', 'data'),
    dash.Output('color-picker', 'style'),
    dash.Output('color-picker', 'label'),
    dash.Output('color-picker', 'value'),
    dash.Input({'group-name': dash.ALL}, 'n_clicks'),
    dash.State('group-choice', 'data'),
    dash.State('graphSettings', 'data'),
    prevent_initial_call=True,
)
def _select_group(n_clicks, choice, settings):
    is_clicked = False
    for n_click in n_clicks:
        is_clicked = is_clicked or n_click
    new_choice = ctx.triggered_id['group-name']

    if not is_clicked or choice == new_choice:
        return None, {'display': 'none'}, 'Color Picker', {'hex': '#119DFF'}
    color = settings['groups'][new_choice]['color']['background']
    return new_choice, {'display': 'block'}, 'Color Picker: ' + new_choice, {'hex': color}

@app.callback(
    dash.Output('graphSettings', 'data', allow_duplicate=True),
    dash.Input('color-picker', 'value'),
    dash.State('group-choice', 'data'),
    dash.State('graphSettings', 'data'),
    prevent_initial_call=True,
)
def _change_color(color, group, settings):
    if group is None:
        raise dash.exceptions.PreventUpdate
    settings['groups'][group]['color']['background'] = color['hex']
    return settings


def build_page():
    return bootstrap.Container(
        [
            bootstrap.Row(
                [
                    bootstrap.Col(bootstrap.Container(id='color-map')),
                    bootstrap.Col(
                        daq.ColorPicker(
                            id='color-picker',
                            label='Color Picker',
                            value={'hex': '#119DFF'},
                        )
                    )
                ]
            )
        ]
    )
