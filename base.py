from requests import Session, Response
from urllib3 import disable_warnings, exceptions
from .exceptions import (
    ApiClientExceptionMessage,
    ApiClientErrors,
    ApiClientException,
    ApiResponseException,
)
import requests.exceptions as re


class ApiConnection:
    headers = {}

    def __init__(self, base_url: str):
        disable_warnings(exceptions.InsecureRequestWarning)
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url
        self.session = Session()

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
        self.session.close()

    def _get_headers(self):
        return self.headers
