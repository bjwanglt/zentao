import copy
import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count, F, Case, Value, CharField, When
from django.http.request import HttpRequest

from web import models
from utils.http_response import SysHttpResponse


def statistics(request: HttpRequest, pid):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    data_type = request.GET.get('data_type')
    if start_str and end_str:
        sys = SysHttpResponse()
        if data_type == 'priority':
            status_dict = dict(models.Issues.status_choices)
            data = list(
                models.Issues.objects.filter(
                    project_id=pid,
                    create_datetime__gte=datetime.datetime.strptime(start_str, '%Y-%m-%d'),
                    create_datetime__lt=datetime.datetime.strptime(end_str, '%Y-%m-%d'),
                ).annotate(name_val=F('status')).values('name_val').annotate(y=Count('*'))
            )
            for d in data:
                d.update(dict(name=status_dict.get(d.get('name_val'))))
                d.pop('name_val')
            sys.status = True
            sys.errors_or_data = data
            return JsonResponse(sys.get_dict())
        if data_type == 'projess':
            data = list(
                models.Issues.objects.filter(
                    project_id=pid,
                    create_datetime__gte=datetime.datetime.strptime(start_str, '%Y-%m-%d'),
                    create_datetime__lt=datetime.datetime.strptime(end_str, '%Y-%m-%d'),
                )
                .annotate(
                    status_display=Case(
                        When(status=1, then=Value('新建')),
                        When(status=2, then=Value('处理中')),
                        When(status=3, then=Value('已解决')),
                        When(status=4, then=Value('已忽略')),
                        When(status=5, then=Value('待反馈')),
                        When(status=6, then=Value('已关闭')),
                        When(status=7, then=Value('重新打开')),
                        output_field=CharField()
                    ),
                    username=Case(
                        When(assign_id=None, then=Value('未指派')),
                        default=F('assign__username'),
                        output_field=CharField()
                    )
                )
                .select_related('assign')
                .values('assign_id', 'username', 'status_display')
            )
            user_list = list({i.get('username') for i in data})
            status_list = list({i.get('status_display') for i in data})
            show_data = {}
            for status in status_list:
                show_data[status] = {u: 0 for u in copy.deepcopy(user_list)}
            for status in status_list:
                for user in user_list:
                    for d in data:
                        if d.get('status_display') == status and d.get('username') == user:
                            show_data[status][user] += 1
            categories = user_list
            series = [dict(name=k, data=list(v.values())) for k, v in show_data.items()]
            sys.status = True
            sys.errors_or_data = dict(categories=categories, series=series)
            return JsonResponse(sys.get_dict())
    else:
        return render(request, 'web/statistics/statistics.html', dict())
