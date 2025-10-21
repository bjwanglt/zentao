import json

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.db.models import Q

from web.form.project_version_demand_form import version_form, demand_form
from web.models import ProjectVersion, ProjectDemand
from utils.http_response import SysHttpResponse
from utils.page_util import get_pagination


def to_version_demand(request: HttpRequest, pid):
    # 获取所有的版本信息
    versions = ProjectVersion.objects.filter(project_id=int(pid)).values('id', 'version')
    return render(request, 'web/version_demand/version_demand.html', dict(version_options=versions))


def version(request: HttpRequest, pid):
    method = request.method
    if method == 'POST':
        res = SysHttpResponse()
        data = request.POST
        if not data.get('id', ''):
            form = version_form(data=data)
        else:
            instance_obj = ProjectVersion.objects.filter(id=data.get('id')).first()
            form = version_form(request.POST, instance=instance_obj)
        if form.is_valid():
            instance = form.save()
            res.status = True
            res.errors_or_data = instance.id
        else:
            res.status = False
            print(f'{form.errors=}')
            res.errors_or_data = form.errors
        return JsonResponse(res.get_dict())
    if method == 'GET':
        page = request.GET.get('page', 1)
        val_id = request.GET.get('id', '')
        val_version = request.GET.get('versiion', '')
        q = Q()
        q.connector = 'AND'
        q.children.append(('project_id', int(pid)))
        if val_id:
            q.children.append(('id', val_id))
        if val_version:
            q.children.append(('version__contains', val_version))

        quereyset = ProjectVersion.objects.select_related('project').values('id', 'project_id', 'project__name',
                                                                            'version').filter(q).order_by('-id')
        return JsonResponse(get_pagination(quereyset, page).get_dict())
    if method == "DELETE":
        sys = SysHttpResponse()
        try:
            body = request.body.decode('utf-8')
            boda_data = json.loads(body)
            ProjectVersion.objects.filter(id=boda_data.get('id')).delete()
            sys.status = True
        except Exception as e:
            sys.status = False
            sys.errors_or_data = str(e)
        finally:
            return JsonResponse(sys.get_dict())


def demand(request: HttpRequest, pid):
    method = request.method
    if method == 'POST':
        res = SysHttpResponse()
        data = request.POST
        if not data.get('id', ''):
            form = demand_form(data=data)
        else:
            instance_obj = ProjectDemand.objects.filter(id=data.get('id')).first()
            form = demand_form(request.POST, instance=instance_obj)
        if form.is_valid():
            form.save()
            res.status = True
        else:
            res.status = False
            print(f'{form.errors=}')
            res.errors_or_data = form.errors
        return JsonResponse(res.get_dict())
    if method == 'GET':
        page = request.GET.get('page', 1)
        val_id = request.GET.get('id', '')
        demand_name = request.GET.get('demand_name', '')
        version_id = request.GET.get('version', '')
        q = Q()
        q.connector = 'AND'
        q.children.append(('version__project_id', int(pid)))
        if val_id:
            q.children.append(('id', val_id))
        if demand_name:
            q.children.append(('demand_name__contains', demand_name))
        if version_id:
            q.children.append(('version_id', int(version_id)))
        quereyset = ProjectDemand.objects.select_related('version', 'project') \
            .values('id', 'demand_name', 'demand_detail', 'version__project_id', 'version__project__name',
                    'version__version', 'version_id') \
            .filter(q).order_by('-id')
        return JsonResponse(get_pagination(quereyset, page).get_dict())
    if method == "DELETE":
        sys = SysHttpResponse()
        try:
            body = request.body.decode('utf-8')
            boda_data = json.loads(body)
            ProjectDemand.objects.filter(id=boda_data.get('id')).delete()
            sys.status = True
        except Exception as e:
            sys.status = False
            sys.errors_or_data = str(e)
        finally:
            return JsonResponse(sys.get_dict())
