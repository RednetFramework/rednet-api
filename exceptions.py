class ApiClientErrors:
    CONNECTION = 2
    TIMEOUT = 3
    INVALID_URL = 4
    INVALID_SCHEMA = 5
    INVALID_REDNET = 6
    UNKNOW = 7

ApiClientExceptionMessage = {
    ApiClientErrors.CONNECTION: 'Error to connect on server',
    ApiClientErrors.TIMEOUT : 'Timeout',
    ApiClientErrors.INVALID_URL : 'Invalid URL',
    ApiClientErrors.INVALID_SCHEMA : 'Invalid Schema',
    ApiClientErrors.UNKNOW : 'Unknow Exception'
}

class ApiResponseException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
    
class ApiClientException(Exception):
    def __init__(self, *args):
        super().__init__(*args)
