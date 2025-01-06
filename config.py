import os
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Union
from pathlib import Path

@dataclass
class RetryConfig:
    enabled: bool = True
    max_attempts: int = 3
    delay: float = 1.0
    backoff: float = 2.0
    max_delay: float = 30.0
    status_codes: list[int] = None

    def __post_init__(self):
        if self.status_codes is None:
            self.status_codes = [408, 429, 500, 502, 503, 504]

@dataclass
class SSLConfig:
    verify: bool = True
    ca_file: Optional[str] = None
    client_cert: Optional[str] = None
    client_key: Optional[str] = None

@dataclass
class TimeoutConfig:
    connect: float = 5.0
    read: float = 30.0
    write: float = 30.0
    pool: float = 30.0

@dataclass
class ApiConfig:
    # Base settings
    base_url: str = 'http://localhost:3000'
    api_prefix: str = ''

    # Authentication
    token: Optional[str] = None
    token_type: str = 'Bearer'

    # SSL/TLS settings
    ssl: SSLConfig = SSLConfig()

    # Request settings
    timeout: TimeoutConfig = TimeoutConfig()
    retry: RetryConfig = RetryConfig()

    # Headers
    default_headers: Dict[str, str] = None
    user_agent: str = 'RednetAPI/1.0'

    def __post_init__(self):
        # Initialize nested dataclasses if they're dictionaries
        if isinstance(self.ssl, dict):
            self.ssl = SSLConfig(**self.ssl)
        if isinstance(self.timeout, dict):
            self.timeout = TimeoutConfig(**self.timeout)
        if isinstance(self.retry, dict):
            self.retry = RetryConfig(**self.retry)
        if self.default_headers is None:
            self.default_headers = {}

    @classmethod
    def from_env(cls) -> 'ApiConfig':
        """Create configuration from environment variables."""
        config_dict = {
            'base_url': os.getenv('REDNET_API_URL', 'http://localhost:3000'),
            'api_prefix': os.getenv('REDNET_API_PREFIX', ''),
            'token': os.getenv('REDNET_API_TOKEN'),
            'token_type': os.getenv('REDNET_API_TOKEN_TYPE', 'Bearer'),
            'user_agent': os.getenv('REDNET_API_USER_AGENT', 'RednetAPI/1.0'),
            'ssl': {
                'verify': os.getenv('REDNET_API_SSL_VERIFY', '').lower() != 'false',
                'ca_file': os.getenv('REDNET_API_SSL_CA_FILE'),
                'client_cert': os.getenv('REDNET_API_SSL_CLIENT_CERT'),
                'client_key': os.getenv('REDNET_API_SSL_CLIENT_KEY')
            },
            'timeout': {
                'connect': float(os.getenv('REDNET_API_TIMEOUT_CONNECT', '5.0')),
                'read': float(os.getenv('REDNET_API_TIMEOUT_READ', '30.0')),
                'write': float(os.getenv('REDNET_API_TIMEOUT_WRITE', '30.0')),
                'pool': float(os.getenv('REDNET_API_TIMEOUT_POOL', '30.0'))
            },
            'retry': {
                'enabled': os.getenv('REDNET_API_RETRY_ENABLED', '').lower() != 'false',
                'max_attempts': int(os.getenv('REDNET_API_RETRY_MAX_ATTEMPTS', '3')),
                'delay': float(os.getenv('REDNET_API_RETRY_DELAY', '1.0')),
                'backoff': float(os.getenv('REDNET_API_RETRY_BACKOFF', '2.0')),
                'max_delay': float(os.getenv('REDNET_API_RETRY_MAX_DELAY', '30.0'))
            }
        }

        # Parse additional headers from environment
        headers_prefix = 'REDNET_API_HEADER_'
        headers = {
            k[len(headers_prefix):].lower().replace('_', '-'): v
            for k, v in os.environ.items()
            if k.startswith(headers_prefix)
        }
        if headers:
            config_dict['default_headers'] = headers

        return cls(**config_dict)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> 'ApiConfig':
        """Load configuration from a JSON file."""
        with open(path, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            k: asdict(v) if hasattr(v, '__dataclass_fields__') else v
            for k, v in asdict(self).items()
        }

    def save(self, path: Union[str, Path]) -> None:
        """Save configuration to a JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    def get_headers(self) -> Dict[str, str]:
        """Get all headers including authorization if token is present."""
        headers = {
            'User-Agent': self.user_agent,
            **self.default_headers
        }
        if self.token:
            headers['Authorization'] = f'{self.token_type} {self.token}'
        return headers

    def get_ssl_context(self):
        """Get SSL context based on configuration."""
        if not self.ssl.verify and not (self.ssl.ca_file or self.ssl.client_cert):
            return False
        import ssl
        context = ssl.create_default_context()
        if self.ssl.ca_file:
            context.load_verify_locations(self.ssl.ca_file)
        if self.ssl.client_cert:
            context.load_cert_chain(
                self.ssl.client_cert,
                self.ssl.client_key
            )
        if not self.ssl.verify:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context

# Create default configuration
config = ApiConfig.from_env()