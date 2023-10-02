from enum import Enum
from json.decoder import JSONDecodeError

import requests


class Method(str, Enum):
    POST = "post"
    GET = "get"
    PATCH = "patch"
    PUT = "put"
    DELETE = "delete"


class RRequest:
    """
    Robust wrapper around Python requests library

    Primary use case is to interact with unstable APIs where responses
    return one-off malformed data or failures
    """

    NUM_RETRIES = 2

    def __init__(self, num_retries=NUM_RETRIES):
        self.num_retries = num_retries

    def get(self, *args, **kwargs):
        return self.request(Method.GET, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request(Method.POST, *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request(Method.PATCH, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request(Method.PUT, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request(Method.DELETE, *args, **kwargs)

    def request(
        self,
        method,
        url,
        params=None,
        data=None,
        headers=None,
        cookies=None,
        files=None,
        auth=None,
        timeout=None,
        allow_redirects=True,
        proxies=None,
        hooks=None,
        stream=None,
        verify=None,
        cert=None,
        json=None,
    ):
        response = self.__default_response()

        for _ in range(self.num_retries):
            response = requests.request(
                method,
                url,
                params=params,
                data=data,
                headers=headers,
                cookies=cookies,
                files=files,
                auth=auth,
                timeout=timeout,
                allow_redirects=allow_redirects,
                proxies=proxies,
                hooks=hooks,
                stream=stream,
                verify=verify,
                cert=cert,
                json=json,
            )

            if response.status_code != 200:
                continue

            try:
                response.json()
            except JSONDecodeError:
                continue
            return response

        if not response.content:
            response.content = "RRequest: Default Error"

        return response

    def __default_response(self):
        response = requests.models.Response
        response.status_code = 400
        return response
