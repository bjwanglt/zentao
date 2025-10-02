import datetime
import time
from functools import wraps

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from utils import ope_cos
from utils.decorators import number_queryparam, number_postparam
from web import models
from django.db.models import Q, F
from utils.http_response import SysHttpResponse
from utils.ope_cache_userinfo import ope_cache_userinfo

empty = JsonResponse(dict())


def parse_none(value, type):
    return None if value in ['None', '', 'null', 'Null', 'undefined'] else type(value)


def get_fullpath_by_fid(pid):
    """找出给定目录或文件所在的完整路径，  示例：/file/folder_aaa/folder_ccc/file_dddd"""
    f_objs = models.ProFile.objects.filter(project_id=pid).values('id', 'file_name', 'parent_id')
    f_objs = {item.get('id'): item for item in f_objs}
    result = []

    # 把父节点加入列表
    def inner(fid):
        # nonlocal result
        if f_objs:
            f_obj = f_objs.get(fid)
            if f_obj:
                result.insert(0, f_obj)
                if not f_obj['parent_id']:
                    return result
                return inner(f_obj['parent_id'])

    def wrapper(fid):
        result.clear()
        inner(fid)
        return '/file/' + '/'.join([f.get('file_name', '') for f in result]), result

    return wrapper


@number_queryparam(['fid'])
def file(request: HttpRequest, pid):
    fid = request.GET.get('fid', None)
    q = Q()
    q.connector = 'AND'
    q.children.append(('project_id', pid))
    q.children.append(('parent_id', fid))
    files_data = models.ProFile.objects.filter(q).all()
    folder_path, file_objs = get_fullpath_by_fid(int(pid))(int(fid) if fid else None)
    return render(request, 'web/file.html',
                  dict(files_data=files_data, folder_path=folder_path, folder_id=fid, file_objs=file_objs))


@csrf_exempt
def upload(request: HttpRequest, pid):
    res = SysHttpResponse()
    userinfo = request.session['userinfo']
    try:
        with transaction.atomic():
            pro_obj = models.Project.objects.filter(id=pid).first()
            # 新增文件记录
            models.ProFile.objects.create(
                parent_id=parse_none(request.POST.get('parent_id'), int),
                file_type=int(request.POST.get('file_type')),
                file_size=int(request.POST.get('file_size')),
                file_name=request.POST.get('file_name'),
                key=request.POST.get('file_key') if int(request.POST.get('file_type')) == 2 else request.POST.get(
                    'file_name'),
                project_id=pid,
                bucket_name=pro_obj.bucket_name,
                create_id=userinfo['userid'],
                create_name=userinfo['username'],
                update_id=userinfo['userid'],
                update_name=userinfo['username'],
                file_path=ope_cos.get_file_url(
                    bucket_name=pro_obj.bucket_name,
                    file_key=request.POST.get('file_key') if int(
                        request.POST.get('file_type')) == 2 else request.POST.get('file_name'),
                    folder_path=request.POST.get('file_path'),
                )
            )
            # 更新已使用空间
            models.Project.objects.filter(id=pid) \
                .update(use_space=F('use_space') + int(request.POST.get('file_size')))
            res.status = True
    except Exception as e:
        print(e)
        res.errors_or_data = str(e)
    finally:
        return JsonResponse(res.get_dict())


@number_postparam(['file_size'])
def get_temp_sign(request: HttpRequest, pid):
    res = SysHttpResponse()
    file_name = request.POST.get('file_name')
    file_size = request.POST.get('file_size')
    folder_path = request.POST.get('folder_path')
    if file_name and folder_path:
        file_name = (str(int(time.time())) + '_' + file_name) if file_size != 0 else (file_name + '/')
        # 1 单文件大小校验
        per_file_size = ope_cache_userinfo.get_user_perfilesize(request.userid)
        if file_size > per_file_size:
            res.errors_or_data = f'单文件大小需小于{per_file_size / 1024 / 1024}M'
            return JsonResponse(res.get_dict())
        # 2 项目剩余空间校验
        pro = models.Project.objects.filter(id=pid).first()
        if file_size + pro.use_space > ope_cache_userinfo.get_user_projectspace(request.userid):
            res.errors_or_data = f'单文件大小需小于{per_file_size}M'
            return JsonResponse(res.get_dict())
        pro_obj = models.Project.objects.filter(id=pid).first()
        # 3 校验通过  返回预签名
        res.status = True
        res.errors_or_data = {
            'upload_url': ope_cos.create_temp_uploadurl(bucket_name=pro_obj.bucket_name, file_name=file_name,
                                                        folder_path=folder_path, file_size=file_size),
            'file_key': file_name
        }
        return JsonResponse(res.get_dict())
    res.errors_or_data('参数错误')
    return JsonResponse(res.get_dict())


def delete(request: HttpRequest, pid):
    """ 删除指定文件 或者 指定项目 """
    res = SysHttpResponse()
    fid = request.POST.get('fid')
    if fid:
        with transaction.atomic():
            # 删除指定文件 恢复项目空间 (防止重复删除)
            file_obj: models.ProFile = models.ProFile.objects.filter(id=fid, file_type=2).select_for_update().first()
            if file_obj:
                # 'https:/jjj-12-1257180138.cos.ap-beijing.myqcloud.com/file/b/1748996249_屏幕截图 2025-01-09 142256.png'
                _path = ope_cos.get_full_filekey(file_obj.file_path,bucket_name=file_obj.bucket_name)
                ope_cos.delete_file(bucket_name=file_obj.bucket_name,file_key=_path)
                models.Project.objects.filter(id=file_obj.project_id).update(
                    use_space=F('use_space') - file_obj.file_size)
                file_obj.delete()
                res.status = True
                return JsonResponse(res.get_dict())
    res.errors_or_data = '参数无效'
    return JsonResponse(res.get_dict())

    # 删除项目 以及 项目下的所有文件


def delete_folder(request: HttpRequest, pid):
    res = SysHttpResponse()
    fid = request.POST.get('fid')
    try:
        with transaction.atomic():
            file_obj: models.ProFile = models.ProFile.objects.filter(id=fid, file_type=1).select_for_update().first()
            delete_path = ope_cos.get_full_filekey(bucket_name=file_obj.bucket_name, file_path=file_obj.file_path) + '/'
            del_dict = ope_cos.delete_folder(bucket_name=file_obj.bucket_name, delete_path=delete_path)
            print(f'{del_dict=}')
            models.ProFile.objects.filter(file_path__in=del_dict['del_path']).delete()
            models.Project.objects.filter(id=file_obj.project_id).update(
                use_space=F('use_space') - del_dict['del_size'])
            res.status = True
    except Exception as e:
        res.errors_or_data = str(e)
    finally:
        return JsonResponse(res.get_dict())
