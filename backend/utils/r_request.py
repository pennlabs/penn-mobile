from enum import Enum
from json.decoder import JSONDecodeError
from typing import Any, Optional

import requests
from requests import Response


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

    def __init__(self, num_retries: int = NUM_RETRIES):
        self.num_retries = num_retries

    def get(self, *args: Any, **kwargs: Any) -> Response:
        return self.request(Method.GET, *args, **kwargs)

    def post(self, *args: Any, **kwargs: Any) -> Response:
        return self.request(Method.POST, *args, **kwargs)

    def patch(self, *args: Any, **kwargs: Any) -> Response:
        return self.request(Method.PATCH, *args, **kwargs)

    def put(self, *args: Any, **kwargs: Any) -> Response:
        return self.request(Method.PUT, *args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> Response:
        return self.request(Method.DELETE, *args, **kwargs)

    def request(
        self,
        method: Method,
        url: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        files: Optional[dict] = None,
        auth: Optional[tuple[str, str]] = None,
        timeout: Optional[int] = None,
        allow_redirects: bool = True,
        proxies: Optional[dict] = None,
        hooks: Optional[dict] = None,
        stream: Optional[bool] = None,
        verify: Optional[bool] = None,
        cert: Optional[str] = None,
        json: Optional[dict] = None,
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

            if not response.ok:
                continue

            try:
                response.json()
            except (TypeError, JSONDecodeError):
                continue
            return response

        if not response.content:
            response.content = "RRequest: Default Error"

        return response

    def __default_response(self) -> requests.models.Response:
        response = requests.models.Response()
        response.status_code = 400
        return response
