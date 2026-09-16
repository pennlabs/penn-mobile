class APIError(ValueError):
    def __init__(self, message: str, status_code=0):
        self.status_code = status_code
        super().__init__(message)
