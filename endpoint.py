from .base import ApiConnection
from .exceptions import ApiResponseException

class ApiEndpointTemplate:
    def __init__(self, client: ApiConnection, endpoint: str):
        self.client = client
        self.endpoint = endpoint

    def _get(self, params=None, path="/"):
        return self.client.request("GET", self.endpoint + path, params=params)

    def _post(self, data: dict = {}, path="", raw=False):
        return self.client.request("POST", self.endpoint + path, raw=raw, json=data)

    def _patch(self, id: str, path: str = "/", data: dict = {}):
        return self.client.request("PATCH", self.endpoint + f"{path}{id}", json=data)

    def _delete(self, id: str, path: str = "/"):
        return self.client.request("DELETE", self.endpoint + f"{path}{id}")

    def find(self, id):
        return self._get(path=f"/{id}")

    def findAll(self):
        return self._get(path="")

    def remove(self, id):
        return self._delete(id)

    def create(self, data):
        return self._post(data=data)

    def update(self, id, data):
        return self._patch(id, data=data)


class AgentEndpoint(ApiEndpointTemplate):
    pass


class AuthEndpoint(ApiEndpointTemplate):
    def auth(
        self, tipo: str, username: str, password: str, data: object = None, **kwargs
    ):
        ret = self._post(
            {"username": username, "password": password, **kwargs},
            path=f"/{tipo}",
        )
        if "token" not in ret:
            raise ApiResponseException("invalid response")

        return ret


class OperatorEndpoint(ApiEndpointTemplate):
    pass


class ListenerEndpoint(ApiEndpointTemplate):
    def __init__(self, client: ApiConnection, endpoint: str):
        super().__init__(client, endpoint)
        self._ws = None

    def connect_ws(self):
        """Connect to listener WebSocket endpoint"""
        self._ws = self.client.connect_websocket("/listener")
        return self._ws

    def disconnect_ws(self):
        """Disconnect from listener WebSocket endpoint"""
        if self._ws:
            self.client.disconnect_websocket("/listener")
            self._ws = None

    def transmit(self, magick: str, data: str):
        """Transmit data using WebSocket if connected, fallback to HTTP"""
        if self._ws:
            self._ws.send_message({
                "type": "listener",
                "action": "response",
                "data": {
                    "magick": magick,
                    "payload": data
                }
            })
        else:
            return self._post({"magick": magick, "data": data}, path="/transmit", raw=True)

    def on_message(self, callback):
        """Register callback for WebSocket messages"""
        if self._ws:
            self._ws.add_callback("listener", callback)

class HandlerEndpoint(ApiEndpointTemplate):
    def __init__(self, client: ApiConnection, endpoint: str):
        super().__init__(client, endpoint)
        self._ws = None

    def connect_ws(self):
        """Connect to handler WebSocket endpoint"""
        self._ws = self.client.connect_websocket("/handler")
        return self._ws

    def disconnect_ws(self):
        """Disconnect from handler WebSocket endpoint"""
        if self._ws:
            self.client.disconnect_websocket("/handler")
            self._ws = None

    def execute_command(self, command: str, args: list = None):
        """Execute a command using WebSocket"""
        if not self._ws:
            raise ApiResponseException("WebSocket not connected")

        self._ws.send_message({
            "type": "command",
            "action": "execute",
            "data": {
                "command": command,
                "args": args or []
            }
        })

    def stream_image(self, image_data: str, metadata: dict):
        """Stream image data using WebSocket"""
        if not self._ws:
            raise ApiResponseException("WebSocket not connected")

        self._ws.send_message({
            "type": "image",
            "action": "stream",
            "data": {
                "image_data": image_data,
                "metadata": metadata
            }
        })

    def on_message(self, callback):
        """Register callback for WebSocket messages"""
        if self._ws:
            self._ws.add_callback("handler", callback)
