from .base import ApiConnection
from .exceptions import ApiResponseException
from typing import Optional, Dict, Any

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
    def execute(self, id: str, command: str, type: str = "shell", timeout: int = 60, metadata: dict = None):
        return self._post(
            {
                "command": command,
                "type": type,
                "timeout": timeout,
                "metadata": metadata or {}
            },
            path=f"/execute/{id}"
        )


class AuthEndpoint(ApiEndpointTemplate):
    def auth(
        self, tipo: str, username: str, password: str, data: object = None, **kwargs
    ):
        ret = self._post(
            {"username": username, "password": password, tipo: data, **kwargs},
            path=f"/{tipo}",
        )
        if "token" not in ret:
            raise ApiResponseException("invalid response")

        return ret


class OperatorEndpoint(ApiEndpointTemplate):
    pass


class ListenerEndpoint(ApiEndpointTemplate):
    def transmit(self, magick: str, data: str):
        return self._post({"magick": magick, "data": data}, path="/transmit", raw=True)

class CommandEndpoint(ApiEndpointTemplate):
    def get_by_uuid(self, uuid: str):
        return self._get(path=f"/{uuid}")

    def get_by_agent(self, agent_uuid: str):
        return self._get(path="", params={"agent_uuid": agent_uuid})

    def get_by_operator(self, operator_uuid: str):
        return self._get(path="", params={"operator_uuid": operator_uuid})

    def update_status(self, uuid: str, status: str, output: Optional[str] = None, error: Optional[str] = None, exit_code: Optional[int] = None):
        data: Dict[str, Any] = {"status": status}
        if output is not None:
            data["output"] = output
        if error is not None:
            data["error"] = error
        if exit_code is not None:
            data["exit_code"] = exit_code
        return self._patch(uuid, data=data)


class HandlerEndpoint(ApiEndpointTemplate):
    def find_by_magick(self, magick: str):
        return self._get(path=f"/magick/{magick}")

    def get_builds(self, handler_id: str):
        return self._get(path=f"/{handler_id}/builds")

    def request_build(self, handler_id: str, options: dict = None):
        return self._post(
            data={"options": options or {}},
            path=f"/{handler_id}/build"
        )
