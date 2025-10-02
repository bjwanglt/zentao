from django.core import serializers
from django.http import HttpRequest, JsonResponse
from django.db import transaction
from django.shortcuts import render
from web.form import pro_manage_forms
from web import models
from utils.http_response import SysHttpResponse
from utils.ope_cache_userinfo import ope_cache_userinfo
from utils import ope_cos
from pypinyin import pinyin, lazy_pinyin, Style


def handle_pro_info(request: HttpRequest):
    """初始化项目标签"""
    userinfo = request.session['userinfo']
    # 返回结果
    results = {
        'star': [],
        'create': [],
        'join': []
    }
    # 所有用户相关项目
    all_pro = models.ProjectUser.objects.filter(user_id=userinfo['userid']). \
        values('project_id', 'star', 'user_name', 'user_role')
    pro_detail = models.Project.objects.filter(id__in=[p.get('project_id') for p in all_pro]).all()
    json_data = serializers.serialize("json", pro_detail)
    print(json_data)
    pro_detail = [{
        'id': p.id,
        'join_count': p.join_count,
        'name': p.name,
        'color': p.get_color_display()
    } for p in pro_detail]
    pro_datail_dict = {p['id']: p for p in pro_detail}
    # 项目信息合并
    pro_info = []
    for p in all_pro:
        id_ = p.pop('project_id')
        pro_info.append({
            **pro_datail_dict[id_], **p
        })
    # 返回结果
    for p in pro_info:
        if p['star']:
            results['star'].append(p)
        results['join'].append(p)
        if p['user_role'] == 1:
            results['create'].append(p)
    return results


def manage_index(request: HttpRequest):
    # 加载项目信息
    pros = handle_pro_info(request)
    # 创建表单
    form = pro_manage_forms.AddProjectForm(request)
    return render(request, 'web/manage/index.html', dict(form=form, pros=pros))


def manage_pro(request: HttpRequest):
    res = SysHttpResponse()
    method = request.method
    userinfo = request.session['userinfo']
    if method == 'POST':
        # user_id = request.session['userinfo']['userid']
        form = pro_manage_forms.AddProjectForm(request, data=request.POST)
        if not form.is_valid():
            res.errors_or_data = form.errors
            return JsonResponse(res.get_dict())
        # 1 校验是否达到项目上限
        pro_list = list(models.Project.objects.filter(create_id=userinfo['userid']).all())
        if len(pro_list) >= (ope_cache_userinfo.get_user_projectnum(userinfo['userid']) or 0):
            res.errors_or_data = dict(desc=['已达项目创建上限，如需添加项目，请选购套餐'])
            return JsonResponse(res.get_dict())
        # 2 校验名称是否重复
        same_name_pro = [pro for pro in pro_list if pro.name == form.cleaned_data['name']]
        if same_name_pro:
            res.errors_or_data = dict(desc=[f'当前项目名称已存在'])
            return JsonResponse(res.get_dict())
        # 3-1 校验无误，新增项目 同时创建人也作为项目参与人
        try:
            with transaction.atomic():
                bucketname = f"{''.join(lazy_pinyin(form.cleaned_data['name']))}-{userinfo['userid']}"
                bucket = ope_cos.create_bucket_with_folder(
                    bucket_name=bucketname,
                    folder_list=['wiki', 'file', 'bug']
                )
                pro_obj = models.Project.objects.create(
                    **form.cleaned_data,
                    create_id=userinfo['userid'],
                    update_id=userinfo['userid'],
                    create_name=userinfo['username'],
                    update_name=userinfo['username'],
                    bucket_name=bucket
                )
                models.ProjectUser.objects.create(
                    user_id=userinfo['userid'],
                    user_name=userinfo['username'],
                    user_role=1, project_id=pro_obj.id,
                    project_name=form.cleaned_data['name']
                )
                res.status = True
        except Exception as e:
            res.errors_or_data = dict(desc=[f'系统繁忙，请稍后重试'])
        finally:
            return JsonResponse(res.get_dict())


def star(request: HttpRequest, pid: int, startype: int):
    # 校验操作项目是否归属当前用户
    res = SysHttpResponse()
    userinfo = request.session['userinfo']
    exists = models.ProjectUser.objects.filter(project_id=pid, user_id=userinfo['userid']).exists()
    if exists:
        models.ProjectUser.objects.filter(project_id=pid, user_id=userinfo['userid']).update(star=bool(int(startype)))
        res.status = True
        return JsonResponse(res.get_dict())
    res.errors_or_data = '无权限操作'
    return JsonResponse(res.get_dict())


def view(request: HttpRequest, pid):
    print(f'{request.proname=}')
    return render(request, 'web/manage/view.html')
