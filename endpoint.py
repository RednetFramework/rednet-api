from .base import ApiConnection
from .exceptions import ApiResponseException
from hashlib import sha256

class ApiEndpointTemplate:
    def __init__(self, client : ApiConnection, endpoint : str):
        self.client = client
        self.endpoint = endpoint

    def _get(self, params=None, path = '/'):
        return self.client.request('GET', self.endpoint + path, params=params )
            
    def _post(self, data : dict = {}, path = '', raw=False):
        return self.client.request('POST', self.endpoint + path, raw=raw, json=data )

    def _patch(self, id: str, path:str = '/', data : dict = {}):
        return self.client.request('PATCH', self.endpoint + f'{path}{id}', json=data )

    def _delete(self, id: str, path: str = '/'):
        return self.client.request('DELETE', self.endpoint + f'{path}{id}')

    def find(self, id):
        return self._get(path=f'/{id}')

    def findAll(self):
        return self._get(path='')

    def remove(self, id):
        return self._delete(id)

    def create(self, data):
        return self._post(data=data)

    def update(self, id, data):
        return self._patch(id, data=data)

class AgentEndpoint(ApiEndpointTemplate):
    pass

class AuthEndpoint(ApiEndpointTemplate):
    def auth(self, tipo: str, username: str, password: str, data: object = None, **kwargs):
        ret = self._post({'username': username, 'password': sha256(password.encode()).hexdigest(), tipo: data, **kwargs }, path=f'/{tipo}')
        if not 'token' in ret:
            raise ApiResponseException('invalid response')

        return ret

class OperatorEndpoint(ApiEndpointTemplate): 
    pass

class ListenerEndpoint(ApiEndpointTemplate):
    def transmit(self, magick: str, data: str):
        return self._post({ 'magick': magick, 'data': data}, path='/transmit', raw=True)

class HandlerEndpoint(ApiEndpointTemplate):
    pass
