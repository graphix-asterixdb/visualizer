class GraphixStatementError(RuntimeError):
    def __init__(self, response_json):
        super().__init__('\n'.join(e['msg'] for e in response_json['errors']))
