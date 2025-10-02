import json
import os
from urllib.parse import quote

from django.conf import settings
from qcloud_cos import CosConfig, CosClientError, CosServiceError
from qcloud_cos import CosS3Client
from functools import wraps

from qcloud_cos.cos_threadpool import SimpleThreadPool
from sts.sts import Sts, CIScope, Scope
from pathlib import Path
from os import path

# 临时密钥生成和使用指引参见 https://cloud.tencent.com/document/product/436/14048

COS_SECRETID = 'AKIDc7QZWGp05ytdBWeZHm392h9QVQAj4GI8'
COS_SECRETKEY = 'gBWeaLtFPTO8f1A8tTnz0qT5XnqjQuCH'

# COS_SECRETID = settings.COS_SECRETID
# COS_SECRETKEY = settings.COS_SECRETKEY
APP_ID = '-1257180138'
REGION = 'ap-beijing'
FOLDER_SUFFIX = '/'
DEFAULT_BUCKET = 'store1'
PUBLIC_PREFIX = f'https://{{}}{APP_ID}.cos.ap-beijing.myqcloud.com/'


def get_full_filekey(file_path: str, bucket_name):
    return file_path.replace(PUBLIC_PREFIX.format(bucket_name), '')


def handle_bucket_name(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if kwargs.get('bucket_name') and str(kwargs.get('bucket_name')).find(APP_ID) == -1:
            kwargs['bucket_name'] = kwargs['bucket_name'] + APP_ID
        return func(*args, **kwargs)

    return inner


# logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def get_cos_client():
    """获取连接"""
    # 1. 设置用户属性
    secret_id = COS_SECRETID
    secret_key = COS_SECRETKEY
    region = REGION
    token = None  # 如果使用永久密钥不需要填入 token,如果使用临时密钥需要填入,
    scheme = None  # 指定使用 http/https 协议来访问 COS,默认为 https,可不填
    # 2 连接
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
    client = CosS3Client(config)
    return client


@handle_bucket_name
def create_bucket(*, bucket_name: str):
    """创建桶"""
    client = get_cos_client()
    client.create_bucket(
        Bucket=bucket_name,
        ACL='public-read',  # ACL='private'|'public-read'|'public-read-write'
    )
    # 配置跨域
    client.put_bucket_cors(
        Bucket=bucket_name,
        CORSConfiguration={
            'CORSRule': [
                {
                    'AllowedOrigin': ['*', ],
                    'AllowedMethod': ['*', ],
                    'AllowedHeader': ['*', ],
                    'ExposeHeader': ['*', ],
                    'MaxAgeSeconds': 500
                }
            ]
        },
    )
    return bucket_name.replace(APP_ID, '').lower()


@handle_bucket_name
def create_bucket_with_folder(*, bucket_name: str, folder_list: list[str]):
    """创建桶,并在桶内创建指定的文件夹"""
    client = get_cos_client()
    client.create_bucket(
        Bucket=bucket_name,
        ACL='public-read',  # ACL='private'|'public-read'|'public-read-write'
    )
    for folder in folder_list:
        upload_file(bucket_name=bucket_name, file_stream=None,
                    file_name=str(folder).replace(FOLDER_SUFFIX, '') + FOLDER_SUFFIX)
    # 配置跨域
    client.put_bucket_cors(
        Bucket=bucket_name,
        CORSConfiguration={
            'CORSRule': [
                {
                    'AllowedOrigin': [
                        '*',
                    ],
                    'AllowedMethod': [
                        'GET', 'PUT', 'HEAD', 'POST', 'DELETE'
                    ],
                    'AllowedHeader': [
                        '*',
                    ],
                    'ExposeHeader': [
                        '*',
                    ]
                }
            ]
        },
    )
    return bucket_name.replace(APP_ID, '').lower()


@handle_bucket_name
def upload_file(*, bucket_name, file_stream, file_name, folder_path: tuple[str] = None):
    """上传文件到指定桶中, 可以携带文件夹路径"""
    prefix = '' if not folder_path else Path(path.join(*folder_path)).as_posix() + '/'
    client = get_cos_client()
    client.put_object(
        Bucket=bucket_name,
        Body=file_stream,
        Key=prefix + file_name,
    )


@handle_bucket_name
def upload_folder(*, bucket_name, folder_name: str):
    """上传文件夹到指定桶中"""
    client = get_cos_client()
    client.put_object(
        Bucket=bucket_name,
        Body=None,
        Key=folder_name.replace(FOLDER_SUFFIX, '') + FOLDER_SUFFIX
    )


@handle_bucket_name
def get_file_url(*, bucket_name, file_key, folder_path: str = None):
    # prefix = '' if not folder_path else Path(path.join(*folder_path)).as_posix() + '/'
    return 'https://' + (f'{bucket_name}.cos.{REGION}.myqcloud.com/{folder_path}/{file_key}'.replace('//', '/'))


@handle_bucket_name
def list_bucket_files(*, bucket_name):
    client = get_cos_client()
    response = client.list_objects(Bucket=bucket_name)
    if 'Contents' in response:
        return response['Contents']


@handle_bucket_name
def get_bucket_used_space(*, bucket_name, folder_list: list[str] = None):
    """查询桶已用空间, 支持指定一级文件夹, 单位B"""
    content_list = list_bucket_files(bucket_name=bucket_name)
    if content_list:
        if not folder_list:
            return sum([int(content.get('Size', '0')) for content in content_list])
        return sum([int(content.get('Size', '0')) for content in content_list if
                    str(content.get('Key', '')).split(FOLDER_SUFFIX, 1)[0] in folder_list])


@handle_bucket_name
def get_temp_credential(*, bucket_name):
    """获取临时凭证"""
    # 临时密钥生效条件,关于condition的详细设置规则和COS支持的condition类型可以参考 https://cloud.tencent.com/document/product/436/71306
    config = {
        'duration_seconds': 60,  # 临时密钥有效时长,单位是秒
        'secret_id': COS_SECRETID,
        'secret_key': COS_SECRETKEY,
        'bucket': bucket_name,
        'region': REGION,
        'allow_prefix': ['*'],
        'allow_actions': ['*'],
    }
    try:
        sts = Sts(config)
        res = sts.get_credential()
        return {k: v for k, v in res['credentials'].items() if k in ['tmpSecretId', 'tmpSecretKey', 'sessionToken']}
    except Exception as e:
        raise Exception('获取临时凭证失败', e)


@handle_bucket_name
def create_temp_uploadurl(*, bucket_name, file_name, folder_path, file_size):
    """生成指定文件大小的预签名"""
    client = get_cos_client()
    url = client.get_presigned_url(
        Method='PUT',
        Bucket=bucket_name,
        Key=folder_path + file_name,
        Headers={
            'x-cos-storage-class': 'STANDARD',
            'Content-Length': file_size
        },
        Expired=3000  # 30秒后过期
    )
    return url


@handle_bucket_name
def delete_file(*, bucket_name, file_key):
    """ 删除指定文件 """
    client = get_cos_client()
    return client.delete_object(
        Bucket=bucket_name,
        Key=file_key
    )


@handle_bucket_name
def delete_folder(*, bucket_name, delete_path):
    client = get_cos_client()
    marker = ''
    del_path = []
    del_size = []
    while True:
        response = client.list_objects(Bucket=bucket_name, Prefix=delete_path, Marker=marker)
        if 'Contents' in response:
            for content in response['Contents']:
                print(f'{content=}')
                del_path.append(content['Key'])
                del_size.append(int(content['Size']))
                client.delete_object(Bucket=bucket_name, Key=content['Key'])
            if response['IsTruncated'] == 'false':
                break
            marker = response['NextMarker']
    return dict(
        del_path=[PUBLIC_PREFIX.format(bucket_name.replace(APP_ID, '')) + (
            f.rsplit('/', 1)[0] if f.endswith('/') else f) for f in del_path],
        del_size=sum(del_size)
    )


if __name__ == '__main__':
    # print(get_full_filekey(bucket_name='jjj-12', file_path='https://jjj-12-1257180138.cos.ap-beijing.myqcloud.com/file/a'))
    # delete_file(bucket_name='jjj-12', file_key='file/a/847.png')
    # print(delete_folder(bucket_name='crm-12', delete_path='file/vvv/'))

    delete_folder(bucket_name='jjj-12', delete_path='file/a/')

    # print(create_temp_uploadurl(bucket_name='crm-12', file_name='屏幕截图 2024-12-30 847.png', folder_path='/file/test3/', file_size=536240))
    # print(create_temp_uploadurl(bucket_name='crm-12', file_name='abcd/', folder_path='/file/test3/', file_size=0))
    # print(get_bucket_used_space(bucket_name='crm-11', folder_list=['wiki']))
    # create_bucket_with_folder(bucket_name='store2', folder_list=['wiki', 'file'])
    # get_bucket_used_space(bucket_name='store1')
    # print(list_bucket_files(bucket_name='store1'))
    # print(get_bucket_used_space(bucket_name='store1'))
    # upload_folder(bucket_name='store1', folder_name='test')
    # print(get_temp_credential(bucket_name='store1'))
