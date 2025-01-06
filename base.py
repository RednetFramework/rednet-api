from requests import Session, Response
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib3 import disable_warnings, exceptions
from typing import Optional, Dict, Any, Union
from .exceptions import (
    ApiClientExceptionMessage,
    ApiClientErrors,
    ApiClientException,
    ApiResponseException,
)
import requests.exceptions as re
from .config import config, ApiConfig


class ApiConnection:
    def __init__(self, base_url: Optional[str] = None, config_file: Optional[str] = None):
        """Initialize API connection with configuration."""
        # Load configuration
        if config_file:
            self.config = ApiConfig.from_file(config_file)
        else:
            self.config = config

        # Override base URL if provided
        if base_url:
            self.config.base_url = base_url.rstrip('/')

        # Initialize session
        self.session = Session()

        # Configure retries
        if self.config.retry.enabled:
            retry_strategy = Retry(
                total=self.config.retry.max_attempts,
                backoff_factor=self.config.retry.backoff,
                status_forcelist=self.config.retry.status_codes
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)

        # Configure timeouts
        self.timeout = (
            self.config.timeout.connect,
            self.config.timeout.read
        )

        # Configure SSL verification
        if not self.config.ssl.verify:
            disable_warnings(exceptions.InsecureRequestWarning)

    def request(self, method: str, endpoint: str, raw: bool = False, **kwargs) -> Union[Dict[str, Any], str]:
        """Make an HTTP request to the API."""
        response: Response
        try:
            # Build URL
            url = f"{self.config.base_url}{self.config.api_prefix}{endpoint}"

            # Set default request options
            kwargs.setdefault('timeout', self.timeout)
            kwargs.setdefault('verify', self.config.get_ssl_context())
            kwargs.setdefault('headers', self.config.get_headers())

            # Make request
            response = self.session.request(method, url, **kwargs)

            # Handle response
            if not response.ok:
                raise ApiResponseException(response.text)

            return response.json() if not raw else response.text

        except re.Timeout:
            raise ApiClientException(ApiClientExceptionMessage[ApiClientErrors.TIMEOUT])
        except re.InvalidURL:
            raise ApiClientException(ApiClientExceptionMessage[ApiClientErrors.INVALID_URL])
        except re.ConnectionError:
            raise ApiClientException(ApiClientExceptionMessage[ApiClientErrors.CONNECTION])
        except re.InvalidSchema:
            raise ApiClientException(ApiClientExceptionMessage[ApiClientErrors.INVALID_SCHEMA])

    def add_header(self, header: str, value: str) -> None:
        """Add a custom header to the default headers."""
        self.config.default_headers[header] = value

    def close_session(self) -> None:
        """Close the HTTP session."""
        self.session.close()
