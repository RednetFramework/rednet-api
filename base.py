from requests import Session, Response
from urllib3 import disable_warnings, exceptions
from .exceptions import (
    ApiClientExceptionMessage,
    ApiClientErrors,
    ApiClientException,
    ApiResponseException,
)
import requests.exceptions as re
from .websocket import WebSocketConnection
from typing import Optional, Dict, Callable


class ApiConnection:
    headers = {}

    def __init__(self, base_url: str):
        disable_warnings(exceptions.InsecureRequestWarning)
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.session = Session()
        self._ws_connections: Dict[str, WebSocketConnection] = {}

    def request(self, method: str, endpoint: str, raw=False, **kwargs):
        response: Response
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(
                method, url, headers=self._get_headers(), verify=False, **kwargs
            )

            if not response.ok:
                raise ApiResponseException(response.text)
            if not raw:
                return response.json()
            else:
                return response.text

        except re.Timeout:
            raise ApiClientException(ApiClientExceptionMessage[ApiClientErrors.TIMEOUT])
        except re.InvalidURL:
            raise ApiClientException(
                ApiClientExceptionMessage[ApiClientErrors.INVALID_URL]
            )
        except re.ConnectionError:
            raise ApiClientException(
                ApiClientExceptionMessage[ApiClientErrors.CONNECTION]
            )
        except re.InvalidSchema:
            raise ApiClientException(
                ApiClientExceptionMessage[ApiClientErrors.INVALID_SCHEMA]
            )

    def add_header(self, header, value):
        self.headers[header] = value

    def close_session(self):
        """Close HTTP session and WebSocket connections"""
        self.session.close()
        for ws in self._ws_connections.values():
            ws.disconnect()
        self._ws_connections.clear()

    def _get_headers(self):
        return self.headers

    def connect_websocket(self, endpoint: str) -> WebSocketConnection:
        """Create and connect to a WebSocket endpoint
        
        Args:
            endpoint: WebSocket endpoint path (e.g., '/handler')
            
        Returns:
            WebSocket connection object
        """
        # Convert HTTP URL to WebSocket URL
        ws_url = self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        ws_url = f"{ws_url}{endpoint}"
        
        # Create WebSocket connection
        ws = WebSocketConnection(ws_url)
        
        # Add headers
        for header, value in self.headers.items():
            ws.set_header(header, value)
            
        # Store connection
        self._ws_connections[endpoint] = ws
        
        # Connect
        ws.connect()
        return ws

    def get_websocket(self, endpoint: str) -> Optional[WebSocketConnection]:
        """Get an existing WebSocket connection
        
        Args:
            endpoint: WebSocket endpoint path
            
        Returns:
            WebSocket connection or None if not found
        """
        return self._ws_connections.get(endpoint)

    def disconnect_websocket(self, endpoint: str):
        """Disconnect a specific WebSocket connection
        
        Args:
            endpoint: WebSocket endpoint path
        """
        if endpoint in self._ws_connections:
            self._ws_connections[endpoint].disconnect()
            del self._ws_connections[endpoint]
