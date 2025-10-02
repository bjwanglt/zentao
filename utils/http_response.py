class SysHttpResponse:

    def __init__(self, status=False, errors_or_data=''):
        self.status = status
        self.errors_or_data = errors_or_data

    def get_dict(self):
        return self.__dict__
