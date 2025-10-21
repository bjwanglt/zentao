import datetime
from collections import defaultdict

from django.db.models import Count, Q
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Value, F
from django.http.request import HttpRequest
from django.db.models.expressions import RawSQL
from django.db.models.functions import Upper, Substr

from web import models
from utils.http_response import SysHttpResponse
from web.models import ProjectDemand, ProjectVersion


def format_user_space(size):
    """ 内存数字展示 """
    if size >= 1024 * 1024 * 1024:
        return "%.2f GB" % (size / (1024 * 1024 * 1024),)
    elif size >= 1024 * 1024:
        return "%.2f MB" % (size / (1024 * 1024),)
    elif size >= 1024:
        return "%.2f KB" % (size / 1024,)
    else:
        return "%d B" % size


def over_view(request: HttpRequest, pid):
    data_type = request.GET.get('data_type')
    # 传递 版本/需求 下拉选数值
    demands = list(ProjectDemand.objects
                   .select_related('version')
                   .filter(version__project_id=36))
    versions = list(ProjectVersion.objects.filter(project_id=36))
    optioin_version = [dict(id=version.id, name=version.version) for version in versions]
    optioin_demand = [dict(id=demand.id, name=demand.demand_name, version=demand.version_id) for demand in demands]
    if not data_type:
        return render(request, 'web/overview/dashboard.html',
                      dict(optioin_version=optioin_version, optioin_demand=optioin_demand))
    sys = SysHttpResponse()
    filter_demand = request.GET.get('demand','')
    filter_version = request.GET.get('version','')
    q = Q()
    q.connector = 'AND'
    if filter_version:
        q.children.append(('version_id', filter_version))
    if filter_demand:
        q.children.append(('demand_id', filter_demand))
    if data_type == 'detail_data':
        # 项目详情
        project_obj: models.Project = models.Project.objects.filter(id=pid).first()
        user_obj: models.UserInfo = models.UserInfo.objects.filter(id=project_obj.create_id).first()
        policy_obj: models.PricePolicy = models.PricePolicy.objects.filter(id=user_obj.price_policy_id).first()
        detail_data = {
            'p_name': project_obj.name,
            'p_desc': project_obj.desc,
            'create_time': project_obj.create_time,
            'use_space': format_user_space(project_obj.use_space),
            'total_space': str(policy_obj.project_space) + 'G',
            'set_menu': policy_obj.title
        }
        sys.status = True
        sys.errors_or_data = detail_data
    if data_type == 'dynamics':
        # 项目最新动态  项目指派 + 问题修改
        # # 指派数据
        assign_data = list(
            models.Issues.objects
            .exclude(assign_id=None)
            .filter(project_id=pid)
            .annotate(type=Value(1), create_time=F('create_datetime'),
                      creator_initial=Upper(Substr('creator__username', 1, 1)))
            .values('type', 'creator__username', 'assign__username', 'id', 'create_time', 'subject', 'creator_initial',
                    'project_id')
            .order_by('-create_datetime')[:10]
        )
        # # 修改数据
        update_data = list(
            models.IssuesReply.objects.filter(reply_type=1)
            .annotate(project_id=Value(pid), type=Value(2), creator_initial=Upper(Substr('creater__username', 1, 1)))
            .values('type', 'creater__username', 'issues_id', 'issues__desc', 'create_time', 'creator_initial',
                    'project_id')
            .order_by('-create_time')[:10]
        )
        assign_data.extend(update_data)
        all_data = sorted(assign_data, key=lambda x: x.get('create_time'), reverse=True)[:10]
        all_data = list(reversed(all_data))
        sys.status = True
        sys.errors_or_data = all_data
    if data_type == 'issue_group':
        status_dict = dict(models.Issues.status_choices)
        data = list(models.Issues.objects.filter(project_id=pid).filter(q).values('status').annotate(num=Count('*')))
        for d in data:
            d.update(dict(status_text=status_dict.get(d.get('status')), project_id=pid))
        sys.status = True
        sys.errors_or_data = data
    if data_type == 'members':
        pre_data = list(models.ProjectUser.objects.filter(project_id=pid).annotate(
            user_avatar=Upper(Substr('user_name', 1, 1))
        ).values('user_role', 'user_name', 'user_avatar'))
        data_creater = [d for d in pre_data if d.get('user_role') == 1]
        data_joiner = [d for d in pre_data if d.get('user_role') == 2]
        sys.status = True
        sys.errors_or_data = dict(data_creater=data_creater, data_joiner=data_joiner)
    if data_type == 'trend':
        pre_data = list(
            models.Issues.objects
            .filter(project_id=pid)
            .filter(q)
            .annotate(create_date=RawSQL('date_format(create_datetime,"%%Y-%%m-%%d")', []))
            .values('create_date').annotate(num=Count('*'))
            .order_by('create_date')
        )
        for d in pre_data:
            d.update(dict(create_date=datetime.datetime.strptime(d.get('create_date'), '%Y-%m-%d').timestamp() * 1000))
        data = [[d.get('create_date'), d.get('num')] for d in pre_data]
        sys.status = True
        sys.errors_or_data = data
    return JsonResponse(sys.get_dict())
