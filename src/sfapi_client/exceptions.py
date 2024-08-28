class SfApiError(Exception):
    """
    Exception indicating an error occurred call the SF API.
    """

    def __init__(self, message):
        self.message = message


class ClientKeyError(Exception):
    """
    Exception indicating an error occurred reading the client keys
    """

    def __init__(self, message):
        self.message = message
