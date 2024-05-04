from .base import ApiConnection
from .endpoint import AgentEndpoint, AuthEndpoint, HandlerEndpoint, ListenerEndpoint, OperatorEndpoint

class Api():
    def __init__(self, connection: ApiConnection) -> None:
        self.connection = connection
        self.auth       = AuthEndpoint(connection, '/auth')
        self.operator   = OperatorEndpoint(connection,  '/operator')
        self.agent      = AgentEndpoint(connection,     '/agent')
        self.handler    = HandlerEndpoint(connection,   '/handler')
        self.listener   = ListenerEndpoint(connection,  '/listener')

    def add_token(self, token: str):
        self.token = token
        self.connection.add_header('Authorization', f'Bearer: {token}')
