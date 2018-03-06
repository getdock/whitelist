from requests import HTTPError


class IDMError(Exception):
    def __init__(self, error: HTTPError):
        self.error = error
        super().__init__()

    @property
    def text(self):
        return self.error.response.text
