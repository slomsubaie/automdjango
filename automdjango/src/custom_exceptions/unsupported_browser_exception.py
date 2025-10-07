class UnsupportedBrowserException(Exception):

    def __init__(self, browserName):
        self.browserName = browserName
        self.message = browserName + " is not supported at the moment"
        super().__init__(self.message)
