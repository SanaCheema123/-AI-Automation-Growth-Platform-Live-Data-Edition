class AppError(Exception):
    def __init__(self, message: str, code: str = "application_error"):
        self.message = message
        self.code = code
        super().__init__(message)
