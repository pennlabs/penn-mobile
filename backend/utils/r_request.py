import enum

import requests


class Method(enum):
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

    NUM_RETRIES = 5

    def __init__(self, num_retries=NUM_RETRIES):
        self.num_retries = num_retries

    def get(self):
        return self.request(Method.GET)

    def post(self):
        return self.request(Method.POST)

    def patch(self):
        return self.request(Method.PATCH)

    def put(self):
        return self.request(Method.PUT)

    def delete(self):
        return self.request(Method.DELETE)

    def request(self, method):
        for _ in range(self.num_retries):
            response = self.__single_request(method)

            # TODO: Test that JSON structure is good
            if response.status_code == 200:
                return response

        # TODO: Return poor status code
        pass

    def __single_request(self, method):
        pass
