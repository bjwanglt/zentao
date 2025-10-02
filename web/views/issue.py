import copy
from redis import Redis
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Q, F
from django.shortcuts import render
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.forms.models import model_to_dict
from django_redis import get_redis_connection

from utils.compnents import CheckFilterCondition
from utils.http_response import SysHttpResponse

from web import models
from web.form.issue_forms import IssusForm, IssueReplayForm, ProjectInviteForm


def issue(request: HttpRequest, pid):
    method = request.method

    if method == 'GET':
        form = IssusForm(request)
        # 分页返回数据
        # # 前端参数处理
        quertdata_dict = dict(project_id=pid)
        query_keys = ['status', 'priority']
        for key in query_keys:
            vals = request.GET.getlist(key)
            if vals:
                quertdata_dict[f'{key}__in'] = vals
        # # 前端查询初始化
        conditions = [
            CheckFilterCondition(request, '状态', 'status', models.Issues.status_choices),
            CheckFilterCondition(request, '优先级', 'priority', models.Issues.priority_choices),
        ]
        queryset = models.Issues.objects.select_related('creator', 'assign').order_by('-id').filter(**quertdata_dict)
        paginator = Paginator(queryset, settings.PAGE_SIZE)
        page = request.GET.get('page', 1)
        issue_datas = paginator.get_page(page)
        # 邀请表单
        invite_form = ProjectInviteForm()
        return render(request, 'web/issue/issues.html',
                      dict(form=form, page_data=issue_datas, conditions=conditions, invite_form=invite_form))
    else:
        form = IssusForm(request, data=request.POST)
        res = SysHttpResponse()
        if form.is_valid():
            form.instance.project_id = pid
            form.instance.creator_id = request.userid
            form.save()
            res.status = True
        else:
            res.errors_or_data = form.errors
        return JsonResponse(res.get_dict())


def issue_detail(request: HttpRequest, pid, issue_id):
    instance = models.Issues.objects.filter(id=issue_id, project_id=pid).first()
    form = IssusForm(request, instance=instance)
    return render(request, 'web/issue/issue_detail.html', dict(form=form, issue_id=issue_id))


def issue_replay(request: HttpRequest, pid, issue_id):
    method = request.method
    # 评论查询
    if method == 'GET':
        # 1 查询条件
        q = Q()
        q.connector = 'AND'
        q.children.append(('issues_id', issue_id))
        parent_id = request.GET.get('parent')
        if parent_id:
            obj_parent = models.IssuesReply.objects.filter(id=int(parent_id)).first()
            q.children.append(('parent_id', parent_id))
            q.children.append(('root', obj_parent.root + 1))
        else:
            q.children.append(('root', 0))
        # 2 分页获取数据
        queryset = models.IssuesReply.objects.filter(q).select_related('creater').order_by('-id').annotate(
            username=F('creater__username')
        )
        paginor = Paginator(queryset, per_page=3)
        page = request.GET.get('page', 1)
        page_data = paginor.get_page(page)
        sys = SysHttpResponse()
        sys.status = True
        # 3 封装分页数据
        data = {
            "results": list(page_data.object_list.values()),  # 转成列表
            "current_page": page_data.number,
            "total_pages": page_data.paginator.num_pages,
            "total_count": page_data.paginator.count,
            "has_next": page_data.has_next(),
            'next_page': page_data.next_page_number() if page_data.has_next() else None,
            "has_previous": page_data.has_previous(),
            "previous_page": page_data.previous_page_number() if page_data.has_previous() else None
        }
        sys.errors_or_data = data
        return JsonResponse(sys.get_dict())
    # 添加 评论/回复
    form = IssueReplayForm(data=request.POST)
    sys = SysHttpResponse()
    obj_parent, obj_created = None, None
    if form.is_valid():
        parent_id = form.cleaned_data.get('parent_id')
        content = form.cleaned_data.get('content')
        try:
            with transaction.atomic():
                # 更新父节点信息
                if parent_id:
                    parent_id = int(parent_id)
                    obj_parent = models.IssuesReply.objects.filter(id=parent_id).first()
                    models.IssuesReply.objects.filter(id=parent_id).update(child_num=F('child_num') + 1)
                # 插入当前节点
                obj_created = models.IssuesReply.objects.create(
                    reply_type=2, issues_id=issue_id, content=content, parent_id=parent_id,
                    root=obj_parent.root + 1 if obj_parent else 0, child_num=0, creater_id=request.userid
                )
                # 返回节点信息，无需页面刷新
                sys.status = True
                obj_created = model_to_dict(obj_created)
                obj_created['username'] = request.username
                obj_created['create_time'] = datetime.now().strftime('%Y-%m-%d')
                if obj_parent:
                    obj_created['parent_username'] = obj_parent.creater.username
                sys.errors_or_data = obj_created
        except Exception as e:
            # TODO 日志记录
            sys.status = False
            sys.errors_or_data = '评论失败'
        return JsonResponse(sys.get_dict())
    else:
        sys.errors_or_data = form.errors
        print(form.errors)
        return JsonResponse(sys.get_dict())


# 根据配置的key, 循环获取最终值
def loop_get_val(obj, key: str):
    key_list = key.split('.')
    for k in key_list:
        obj = getattr(obj, k)
        if obj is None:
            return None
        if callable(obj):
            obj = obj()
    return obj


def get_edit_content(old: models.Issues, new: models.Issues):
    result = []
    compare_field_dict = {
        'module.title': '模块',
        'subject': '主题',
        'get_priority_display': '优先级',
        'get_status_display': '状态',
        'start_date': '开始时间',
        'end_date': '结束时间',
    }
    for key in compare_field_dict.keys():
        attr_old = loop_get_val(old, key)
        attr_new = loop_get_val(new, key)
        if attr_old != attr_new:
            result.append(f'{compare_field_dict[key]}: {attr_old}==>{attr_new};')
    if result:
        result.insert(0, '修改内容：')
        return '\n'.join(result)
    return ''


def issue_edit(request, pid, issue_id):
    obj_old = models.Issues.objects.filter(id=issue_id).first()
    obj_old_copy = copy.deepcopy(obj_old)
    form = IssusForm(request, data=request.POST, instance=obj_old)
    sys = SysHttpResponse()
    if form.is_valid():
        try:
            with transaction.atomic():
                # 1 数据修改
                obj_new = form.save()
                # 2 插入一条修改记录至问题评论
                content = get_edit_content(obj_old_copy, obj_new)
                if content:
                    models.IssuesReply.objects.create(
                        reply_type=1, issues_id=issue_id, content=content, creater_id=request.userid,
                        root=0, child_num=0
                    )
                sys.status = True
        except Exception as e:
            sys.status = False
            sys.errors_or_data = dict(subject=[str(e)])
    else:
        sys.errors_or_data = form.errors
    return JsonResponse(sys.get_dict())


from uuid import uuid4


def get_invite_code():
    return str(uuid4())


def get_invite_url(request: HttpRequest, pid):
    form = ProjectInviteForm(request.POST)
    sys = SysHttpResponse()
    if form.is_valid():
        # 生成邀请码，加入缓存，返回邀请链接
        redis_client: Redis = get_redis_connection('default')
        cleaned_data = form.cleaned_data
        invite_code = get_invite_code()
        cache_data = dict(
            limit_num=cleaned_data.get('limit_num'), use_count=0, project_id=pid, creater_id=request.userid
        )
        redis_client.hset(invite_code, mapping=cache_data)
        redis_client.expire(invite_code, cleaned_data.get('expire'))
        sys.status = True
        sys.errors_or_data = f'{request.scheme}://{request.get_host()}/account/invite?code={invite_code}'
    else:
        sys.errors_or_data = form.errors
    return JsonResponse(sys.get_dict())


def invite(request: HttpRequest):
    invite_code = request.GET.get('code')
    if invite_code:
        # 校验是否有效
        redis_client: Redis = get_redis_connection('default')
        cache_data_encode = redis_client.hgetall(invite_code)
        if cache_data_encode:
            # 缓存有效
            cache_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in cache_data_encode.items()}
            # # 校验邀请相关规则
            limit_num = cache_data.get('limit_num', float('inf'))
            use_num = cache_data.get('use_count')
            if use_num >= limit_num:
                # 人数邀请码设置的上限 请求失败
                return render(request, 'web/manage/invite_join.html', dict(error='超过邀请人数上线'))
            project_id = int(cache_data.get('project_id'))
            if request.userid in list(
                    models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id', flat=True)):
                # 已在项目成员中，请求失败
                return render(request, 'web/manage/invite_join.html', dict(error='已在项目成员中'))
            # # 校验项目约束
            try:
                with transaction.atomic():
                    project_obj: models.Project = models.Project.objects.filter(
                        id=project_id).select_for_update().first()
                    joined_count = project_obj.join_count
                    project_max_count_encode = redis_client.hget('sys_cache_user_info_' + cache_data.get('creater_id'),
                                                                 'project_member')
                    project_max_count = int(project_max_count_encode.decode('utf-8'))
                    # # 校验通过
                    if joined_count < project_max_count:
                        # 处理加入逻辑  项目join_count+1  /  project_user插入数据 / 缓存中加入人数+1
                        models.Project.objects.filter(id=project_id).update(
                            join_count=F('join_count') + 1
                        )
                        models.ProjectUser.objects.create(
                            user_id=request.userid, user_name=request.username,
                            user_role=2, project_id=project_id, project_name=project_obj.name
                        )
                        redis_client.hincrby(invite_code, 'use_count', 1)
                        return render(request, 'web/manage/invite_join.html', dict(
                            to_url=f'{request.scheme}://{request.get_host()}/account/manage_index/'
                        ))
                    else:
                        # 达到套餐上线 请求失败
                        return render(request, 'web/manage/invite_join.html',
                                      dict(error='达到套餐项目成员数上线，请联系项目创建者升级套餐'))
            except Exception as e:
                print(e)
                return render(request, 'web/manage/invite_join.html', dict(error='加入失败'))
        else:
            # 缓存失效 请求失败
            return render(request, 'web/manage/invite_join.html', dict(error='邀请链接失效，请联系项目创建者重新邀请'))
    else:
        # 无邀请码 请求失败
        return render(request, 'web/manage/invite_join.html', dict(error='无邀请码，请求失败'))
