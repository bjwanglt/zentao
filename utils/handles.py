from django.core.files.uploadhandler import FileUploadHandler
from django.conf import settings

from utils.ope_cache_userinfo import ope_cache_userinfo


class MaxSizeFileUploadHandler(FileUploadHandler):
    def __init__(self, request=None):
        super().__init__(request)
        per_file_size = ope_cache_userinfo.get_user_perfilesize(request.userid)
        self.max_size = per_file_size if per_file_size else 0
        self.total_upload = 0

    def receive_data_chunk(self, raw_data, start):
        # 目前只针对Wiki的图片上传，后期再看是否调整
        if self.request.resolver_match.url_name == 'wiki_upload':
            self.total_upload += len(raw_data)
            if self.total_upload > self.max_size:
                raise Exception(settings.FILE_UPLOAD_MAX_MEMORY_SIZE_ERROR)
        return raw_data

    def file_complete(self, file_size):
        return None
