"""Only static reason codes cross the HTTP/logging boundary."""
class Rejected(ValueError):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)
