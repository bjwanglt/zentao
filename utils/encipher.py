import hashlib
from django.conf import settings

CODE = 'utf-8'


def md5(val: str):
    md5_obj = hashlib.md5(settings.SECRET_KEY.encode(CODE))
    md5_obj.update(val.encode(CODE))
    return md5_obj.hexdigest()
