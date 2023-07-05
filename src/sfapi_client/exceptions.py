class SfApiError(Exception):
    """
    Exception indicating an error occurred call the SF API.
    """

    def __init__(self, message):
        self.message = message
