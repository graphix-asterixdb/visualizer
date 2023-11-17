import dash
import dash_bootstrap_components as bootstrap

app = dash.Dash(
    __name__,
    title='Graphix Query Console',
    suppress_callback_exceptions=True,
    external_stylesheets=[
        bootstrap.themes.COSMO,
        "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css",
        'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.9.1/font/bootstrap-icons.css'
    ]
)

QUERY_DIRECTORY = '/'
METADATA_DIRECTORY = '/metadata/'
FUNCTIONS_DIRECTORY = '/builtin-functions/'
SETTINGS_DIRECTORY = '/settings/'
