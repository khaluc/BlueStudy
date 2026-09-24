class ExtractionError(Exception):
    def __init__(self, code, detail=None):
        self.code = code
        self.detail = detail or code
        super().__init__(self.detail)
