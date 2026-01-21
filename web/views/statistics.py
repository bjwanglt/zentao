import copy
import datetime

from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Count, F, Case, Value, CharField, When, Q
from django.http.request import HttpRequest

from web import models
from utils.http_response import SysHttpResponse
from web.models import ProjectDemand, ProjectVersion

from pyecharts import options as opts
from pyecharts.charts import Pie, Bar
from pyecharts.commons.utils import JsCode


def generate_priority_chart(start_str, end_str, pid, version, demand):
    """生成优先级统计饼图"""
    q = Q()
    q.connector = 'AND'
    if version:
        q.children.append(('version_id', version))
    if demand:
        q.children.append(('demand_id', demand))
    
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
    
    # 准备饼图数据
    pie_data = []
    for d in data:
        status_name = status_dict.get(d.get('name_val'))
        pie_data.append([status_name, d.get('y')])
    
    # 创建饼图
    pie = (
        Pie()
        .add(
            "优先级",
            pie_data,
            radius=["40%", "75%"],
            center=["50%", "60%"],
            label_opts=opts.LabelOpts(
                is_show=True,
                formatter="{b}: {c} ({d}%)"
            ),
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="优先级统计", pos_left="center", pos_top="20"),
            legend_opts=opts.LegendOpts(
                orient="vertical",
                pos_top="15%",
                pos_left="2%"
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{a} <br/>{b}: {c} ({d}%)"
            ),
        )
        .set_colors(["#3498db", "#e74c3c", "#f39c12", "#27ae60", "#9b59b6", "#95a5a6"])
    )
    
    return pie.render_embed()


def generate_project_user_chart(start_str, end_str, pid, version, demand):
    """生成人员工作进度柱状图"""
    q = Q()
    q.connector = 'AND'
    if version:
        q.children.append(('version_id', version))
    if demand:
        q.children.append(('demand_id', demand))
    
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
    
    # 创建柱状图
    bar = (
        Bar()
        .add_xaxis(user_list)
        .add_yaxis(
            "新建",
            list(show_data.get('新建', {}).values()),
            stack="总量",
            color="#3498db"
        )
        .add_yaxis(
            "处理中",
            list(show_data.get('处理中', {}).values()),
            stack="总量",
            color="#f39c12"
        )
        .add_yaxis(
            "已解决",
            list(show_data.get('已解决', {}).values()),
            stack="总量",
            color="#27ae60"
        )
        .add_yaxis(
            "已忽略",
            list(show_data.get('已忽略', {}).values()),
            stack="总量",
            color="#95a5a6"
        )
        .add_yaxis(
            "待反馈",
            list(show_data.get('待反馈', {}).values()),
            stack="总量",
            color="#9b59b6"
        )
        .add_yaxis(
            "已关闭",
            list(show_data.get('已关闭', {}).values()),
            stack="总量",
            color="#34495e"
        )
        .add_yaxis(
            "重新打开",
            list(show_data.get('重新打开', {}).values()),
            stack="总量",
            color="#e74c3c"
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="人员工作进度", pos_left="center", pos_top="20"),
            xaxis_opts=opts.AxisOpts(name="人员"),
            yaxis_opts=opts.AxisOpts(name="问题数量"),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="shadow",
                formatter=JsCode("""
                    function(params) {
                        var total = 0;
                        var result = params[0].name + '<br/>';
                        for (var i = 0; i < params.length; i++) {
                            result += params[i].marker + params[i].seriesName + ': ' + params[i].value + '<br/>';
                            total += params[i].value;
                        }
                        result += '总量: ' + total;
                        return result;
                    }
                """)
            ),
            legend_opts=opts.LegendOpts(pos_top="10%"),
        )
    )
    
    return bar.render_embed()


def statistics(request: HttpRequest, pid):
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')
    data_type = request.GET.get('data_type')
    if start_str and end_str:
        version = request.GET.get('version','')
        demand = request.GET.get('demand','')
        
        if data_type == 'priority':
            # 生成优先级饼图
            chart_html = generate_priority_chart(start_str, end_str, pid, version, demand)
            return JsonResponse({'status': True, 'chart_html': chart_html})
            
        if data_type == 'projess':
            # 生成人员工作进度柱状图
            chart_html = generate_project_user_chart(start_str, end_str, pid, version, demand)
            return JsonResponse({'status': True, 'chart_html': chart_html})
    else:
        # 传递 版本/需求 下拉选数值
        demands = list(ProjectDemand.objects
                       .select_related('version')
                       .filter(version__project_id=int(pid)))
        versions = list(ProjectVersion.objects.filter(project_id=int(pid)))
        optioin_version = [dict(id=version.id, name=version.version) for version in versions]
        optioin_demand = [dict(id=demand.id, name=demand.demand_name, version=demand.version_id) for demand in demands]
        return render(request, 'web/statistics/statistics.html', dict(optioin_version=optioin_version, optioin_demand=optioin_demand))
