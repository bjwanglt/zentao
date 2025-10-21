import json

from celery.result import AsyncResult
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.db.models import Q
from django_celery_results.models import TaskResult
from zentao import celery_app

from utils.page_util import get_pagination
from web.form.schedule_job_forms import job_form
from django_celery_beat.models import PeriodicTask
from utils.http_response import SysHttpResponse


def to_schedule_job(request: HttpRequest, pid):
    return render(request, 'web/schedule_job/schedule_job.html', dict(form=job_form(request=request)))


def schedule_job_retry(request: HttpRequest, pid):
    task_id = request.POST.get('task_id', '')
    task_name = request.POST.get('task_name', '')
    res = None
    sys = SysHttpResponse(False, '参数有误')
    if not task_id:
        return JsonResponse(sys.get_dict())
    res = AsyncResult(task_id, app=celery_app)
    if not res:
        return JsonResponse(sys.get_dict())
    args = res.args
    args = args.replace("'", '"')
    args = json.loads(args)
    task = celery_app.tasks[task_name]
    task.apply_async(args=args, headers={'django-celery-beat': {'periodic_task_name': 'ceshi7'}})
    sys.status = True
    return JsonResponse(sys.get_dict())


def schedule_job_result(request: HttpRequest, pid):
    page = request.GET.get('page', 1)
    periodic_task_name = request.GET.get('periodic_task_name', '')
    queryset = TaskResult.objects.filter(periodic_task_name=periodic_task_name).values(
        'task_id', 'status', 'date_created', 'date_done', 'task_args', 'task_name', 'result'
    ).order_by('-date_created')
    res = get_pagination(queryset, page)
    return JsonResponse(res.get_dict())


def schedule_job(request: HttpRequest, pid):
    method = request.method
    if method == 'GET':
        print(request.GET)
        page = request.GET.get('page', 1)
        name = request.GET.get('name', '')
        task_id = request.GET.get('task_id', '')
        q = Q()
        q.connector = 'AND'
        if name:
            q.children.append(('name__contains', name))
        if task_id:
            q.children.append(('id', task_id))
        queryset = PeriodicTask.objects.exclude(name__startswith='celery.').select_related('interval', 'crontab') \
            .values('name', 'args', 'id', 'crontab__hour', 'crontab__minute', 'interval__every', 'interval__period',
                    'enabled', 'task', 'crontab__hour', 'crontab__minute').filter(q).order_by('-id')
        for i in queryset:
            i['args'] = ';'.join(json.loads(i['args'])[0])
        res = get_pagination(queryset, page)
        return JsonResponse(res.get_dict())
    if method == 'POST':
        res = SysHttpResponse()
        form = job_form(request=request, data=request.POST)
        if form.is_valid():
            # 数据无误 保存数据
            form.cleaned_data.pop('scheduler_hour')
            form.cleaned_data.pop('scheduler_minute')
            form.cleaned_data.pop('project_id')
            instance_id = form.cleaned_data.get('id', '')
            try:
                if not instance_id:
                    PeriodicTask.objects.create(
                        **form.cleaned_data, enabled=1
                    )
                else:
                    PeriodicTask.objects.filter(id=instance_id).update(
                        **form.cleaned_data
                    )
                res.status = True
            except Exception as e:
                res.status = False
                res.errors_or_data = '数据保存失败'
            finally:
                return JsonResponse(res.get_dict())
        else:
            res.status = False
            res.errors_or_data = form.errors
            print(f'{form.errors=}')
            return JsonResponse(res.get_dict())
    if method == 'PATCH':
        res = SysHttpResponse()
        body_data = request.body.decode('utf-8')
        pairs = body_data.split('&')
        data = {}
        for pair in pairs:
            key, value = pair.split('=')
            data[key] = value

        id = data.get('id', None)
        enabled = data.get('enabled', None)
        if id is not None and enabled is not None:
            try:
                PeriodicTask.objects.filter(id=id).update(enabled=(enabled == 'true'))
                res.status = True
            except Exception as e:
                res.status = False
                res.errors_or_data = '操作失败，请稍后重试'
            finally:
                return JsonResponse(res.get_dict())
        else:
            res.status = False
            res.errors_or_data = '参数有误'
            return JsonResponse(res.get_dict())
    if method == "DELETE":
        res = SysHttpResponse()
        body = request.body.decode('utf-8')
        if body:
            data = json.loads(body)
            id = data.get('id')
            if id is not None:
                try:
                    PeriodicTask.objects.filter(id=id).delete()
                    res.status = True
                except Exception as e:
                    res.status = False
                    res.errors_or_data = '操作失败，请稍后重试'
                finally:
                    return JsonResponse(res.get_dict())
            else:
                res.status = False
                res.errors_or_data = '参数有误'
                return JsonResponse(res.get_dict())
