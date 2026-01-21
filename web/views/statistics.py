import copy
import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count, F, Case, Value, CharField, When, Q
from django.http.request import HttpRequest

from web import models
from utils.http_response import SysHttpResponse
from web.models import ProjectDemand, ProjectVersion

from pyecharts.charts import Pie, Bar
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from django.http import HttpResponse


def statistics(request: HttpRequest, pid):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    data_type = request.GET.get('data_type')
    if start_str and end_str:
        version = request.GET.get('version','')
        demand = request.GET.get('demand','')
        q = Q()
        q.connector = 'AND'
        if version:
            q.children.append(('version_id', version))
        if demand:
            q.children.append(('demand_id', demand))
        sys = SysHttpResponse()
        if data_type == 'priority':
            status_dict = dict(models.Issues.status_choices)
            data = list(
                models.Issues.objects
                .filter(
                    project_id=pid,
                    create_datetime__gte=datetime.datetime.strptime(start_str, '%Y-%m-%d'),
                    create_datetime__lt=datetime.datetime.strptime(end_str, '%Y-%m-%d'),
                )
                .filter(q)
                .annotate(name_val=F('status')).values('name_val').annotate(y=Count('*'))
            )
            pie_data = []
            for d in data:
                name = status_dict.get(d.get('name_val'))
                y = d.get('y')
                pie_data.append((name, y))
            # 使用pyecharts生成饼图
            pie = Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="400px", height="300px"))
            pie.add("优先级", pie_data)
            pie.set_global_opts(
                title_opts=opts.TitleOpts(title=None),
                legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="5%"),
                tooltip_opts=opts.TooltipOpts(formatter="{a} <br/>{b}: {c}")
            )
            pie.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
            return HttpResponse(pie.render_embed())
        if data_type == 'projess':
            data = list(
                models.Issues.objects.filter(
                    project_id=pid,
                    create_datetime__gte=datetime.datetime.strptime(start_str, '%Y-%m-%d'),
                    create_datetime__lt=datetime.datetime.strptime(end_str, '%Y-%m-%d'),
                )
                .filter(q)
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
            # 使用pyecharts生成柱状图
            bar = Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="700px", height="300px"))
            bar.add_xaxis(user_list)
            for status in status_list:
                bar.add_yaxis(status, [show_data[status][user] for user in user_list])
            bar.set_global_opts(
                title_opts=opts.TitleOpts(title=None),
                xaxis_opts=opts.AxisOpts(name="人员"),
                yaxis_opts=opts.AxisOpts(name="问题数量"),
                legend_opts=opts.LegendOpts(orient="horizontal", pos_top="10%", pos_left="center"),
                tooltip_opts=opts.TooltipOpts(formatter="{a} <br/>{b}: {c}")
            )
            return HttpResponse(bar.render_embed())
    else:
        # 传递 版本/需求 下拉选数值
        demands = list(ProjectDemand.objects
                       .select_related('version')
                       .filter(version__project_id=int(pid)))
        versions = list(ProjectVersion.objects.filter(project_id=int(pid)))
        optioin_version = [dict(id=version.id, name=version.version) for version in versions]
        optioin_demand = [dict(id=demand.id, name=demand.demand_name, version=demand.version_id) for demand in demands]
        return render(request, 'web/statistics/statistics.html', dict(optioin_version=optioin_version, optioin_demand=optioin_demand))
